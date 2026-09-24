import re
from typing import Dict, List, Tuple
from collections import defaultdict
from difflib import SequenceMatcher
from Levenshtein import distance as levenshtein_distance


class CParser:
    """Анализирует только внешний вид и чистоту кода"""

    def __init__(self, code: str):
        self.code = code
        self.lines = code.split('\n')
        self.stats = defaultdict(int)
        self.lists = defaultdict(list)
        self.variables = []
        self.similar_pairs = []
        self.stats['complex_code_commented_ratio'] = 0
        self.stats['meaningful_comment_ratio'] = 0
        self.stats['useless_comment_count'] = 0

    def extract_metrics(self) -> Dict[str, float]:
        """Извлекает все метрики чистоты кода"""
        self._count_lines()
        self._analyze_comments()
        self._extract_variables()
        self._analyze_naming()
        self._analyze_naming_similarity()
        self._analyze_anti_patterns()
        self._analyze_formatting()
        self._analyze_comments_quality()
        self._analyze_comment_meaningfulness()
        return self._compute_metrics()

    def _count_lines(self):
        """Подсчет строк кода"""
        self.stats['total_lines'] = len(self.lines)
        self.stats['non_empty_lines'] = sum(1 for l in self.lines if l.strip())
        self.stats['code_lines'] = sum(1 for l in self.lines
                                       if l.strip() and not l.strip().startswith('//'))
        self.stats['blank_lines'] = sum(1 for l in self.lines if not l.strip())
        self.stats['max_line_length'] = max((len(l.rstrip()) for l in self.lines), default=0)

    def _extract_variables(self):
        """Извлечение переменных из кода"""
        keywords = {'int', 'char', 'void', 'return', 'if', 'else', 'for', 'while',
                    'class', 'struct', 'public', 'private', 'protected', 'const',
                    'static', 'virtual', 'using', 'namespace', 'template', 'auto',
                    'nullptr', 'true', 'false', 'new', 'delete', 'try', 'catch',
                    'main', 'include', 'define', 'sizeof', 'decltype', 'noexcept'}

        variables = set()
        patterns = [

            r'\b(?:int|float|double|char|bool|long|short|auto|unsigned|signed)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[=;,]',

            r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=[^=]',

            r'for\s*\([^;]*;\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*[<>=!]',
            r'for\s*\([^;]*;\s*[^;]*;\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*[++\-)]',

            r'\([^)]*?\b(?:int|float|double|char|bool)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, self.code)
            for match in matches:
                var_name = match if isinstance(match, str) else match[0]
                if var_name not in keywords and not var_name.isdigit():
                    variables.add(var_name)

        self.variables = list(variables)

    def _analyze_comments(self):
        """Анализ комментариев"""
        comment_lines = 0
        doxygen_lines = 0
        in_multiline = False

        for line in self.lines:
            stripped = line.strip()

            if stripped.startswith('//'):
                comment_lines += 1
                if '@param' in stripped or '@return' in stripped or 'brief' in stripped:
                    doxygen_lines += 1
            elif '/*' in stripped:
                in_multiline = True
                comment_lines += 1
            elif '*/' in stripped:
                in_multiline = False
                comment_lines += 1
            elif in_multiline:
                comment_lines += 1
                if '@param' in stripped or '@return' in stripped or 'brief' in stripped:
                    doxygen_lines += 1

        self.stats['comment_lines'] = comment_lines
        self.stats['doxygen_lines'] = doxygen_lines
        self.stats['comment_density'] = comment_lines / max(1, self.stats['code_lines'])

    def _normalize_name(self, name: str) -> str:
        """Нормализация названия переменной для сравнения"""
        name = name.lower()
        name = re.sub(r'\d+', '#', name)
        name = name.replace('_', ' ')
        name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        name = name.lower()
        return name.strip()

    def _jaccard_ngrams(self, s1: str, s2: str, n: int = 2) -> float:
        """Jaccard similarity на n-граммах"""
        def get_ngrams(s: str):
            s = s.replace(' ', '')
            if len(s) < n:
                return {s}
            return set(s[i:i + n] for i in range(len(s) - n + 1))

        grams1 = get_ngrams(s1)
        grams2 = get_ngrams(s2)

        if not grams1 or not grams2:
            return 0.0

        intersection = len(grams1 & grams2)
        union = len(grams1 | grams2)
        return intersection / union if union > 0 else 0.0

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Расчет схожести двух идентификаторов"""
        if name1 == name2:
            return 1.0

        n1 = self._normalize_name(name1)
        n2 = self._normalize_name(name2)

        if n1 == n2:
            return 1.0

        max_len = max(len(n1), len(n2), 1)
        lev_sim = 1 - levenshtein_distance(n1, n2) / max_len

        seq_sim = SequenceMatcher(None, n1, n2).ratio()

        ngram_sim = self._jaccard_ngrams(n1, n2, n=2)

        if len(n1) <= 2 and len(n2) <= 2:
            return 0.0
        elif (len(n1) <= 2) != (len(n2) <= 2):
            return 0.2

        return lev_sim * 0.3 + seq_sim * 0.4 + ngram_sim * 0.3

    def _is_confusing_pair(self, name1: str, name2: str) -> bool:
        """Проверка на запутывающие пары (частая ошибка новичков)"""

        # Паттерн 1: value1 и value2
        if re.match(r'^\w+1$', name1) and re.match(r'^\w+2$', name2):
            # Проверяем, что основа одинаковая
            base1 = name1[:-1]  # убираем '1'
            base2 = name2[:-1]  # убираем '2'
            if base1 == base2:
                return True

        # Паттерн 2: i1 и j1, i2 и j2
        if re.match(r'^[ij]\d+$', name1) and re.match(r'^[ij]\d+$', name2):
            num1 = re.search(r'\d+$', name1).group()
            num2 = re.search(r'\d+$', name2).group()
            if num1 == num2:  # i1 и j1
                return True

        # Паттерн 3: temp и tmp
        temp_variants = ['temp', 'tmp', 'temporary']
        if name1 in temp_variants and name2 in temp_variants and name1 != name2:
            return True

        # Паттерн 4: arr и array
        arr_variants = ['arr', 'array', 'arrray']
        if name1 in arr_variants and name2 in arr_variants and name1 != name2:
            return True

        # Паттерн 5: user_name и username (убираем подчеркивание)
        if '_' in name1 and '_' not in name2:
            if name1.replace('_', '') == name2:
                return True
        if '_' in name2 and '_' not in name1:
            if name2.replace('_', '') == name1:
                return True

        return False

    def _analyze_naming_similarity(self):
        """Анализ схожести названий переменных между собой"""
        if len(self.variables) < 2:
            self.stats['naming_similarity_score'] = 0.0
            self.stats['too_similar_pairs_ratio'] = 0.0
            self.stats['confusing_pairs_count'] = 0
            return

        similarities = []
        confusing_count = 0

        for i, var1 in enumerate(self.variables):
            for var2 in self.variables[i + 1:]:
                sim = self._calculate_name_similarity(var1, var2)
                similarities.append(sim)

                if self._is_confusing_pair(var1, var2):
                    confusing_count += 1
                    self.lists['confusing_pairs'].append((var1, var2))

                if sim > 0.7:
                    self.lists['similar_pairs'].append((var1, var2, sim))

        if similarities:
            # Средняя схожесть (чем ниже, тем лучше)
            avg_similarity = sum(similarities) / len(similarities)

            # Доля слишком похожих пар (>0.7)
            too_similar = [s for s in similarities if s > 0.7]
            too_similar_ratio = len(too_similar) / len(similarities)

            # Максимальная схожесть
            max_similarity = max(similarities)

            self.stats['naming_similarity_score'] = avg_similarity
            self.stats['too_similar_pairs_ratio'] = too_similar_ratio
            self.stats['max_naming_similarity'] = max_similarity
            self.stats['confusing_pairs_count'] = confusing_count
        else:
            self.stats['naming_similarity_score'] = 0.0
            self.stats['too_similar_pairs_ratio'] = 0.0
            self.stats['max_naming_similarity'] = 0.0
            self.stats['confusing_pairs_count'] = 0

    def _analyze_naming(self):
        """Анализ качества именования"""
        keywords = {'int', 'char', 'void', 'return', 'if', 'else', 'for', 'while',
                    'class', 'struct', 'public', 'private', 'protected', 'const',
                    'static', 'virtual', 'using', 'namespace', 'template', 'auto',
                    'nullptr', 'true', 'false', 'new', 'delete', 'try', 'catch',
                    'main', 'include', 'define', 'sizeof', 'decltype', 'noexcept'}

        identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', self.code)
        real_identifiers = [id for id in identifiers
                            if id not in keywords and not id.isdigit()]

        if not real_identifiers:
            self.stats['meaningful_names_ratio'] = 0
            self.stats['naming_consistency'] = 1.0
            self.stats['avg_identifier_len'] = 0
            return

        # Определяем осмысленные имена (длина > 2 или не счетчик цикла)
        loop_counters = {'i', 'j', 'k', 'n', 'm', 'x', 'y', 'z'}
        meaningful = [id for id in real_identifiers
                      if len(id) > 2 or id not in loop_counters]

        self.stats['meaningful_names_ratio'] = len(meaningful) / len(real_identifiers)
        self.stats['avg_identifier_len'] = sum(len(id) for id in real_identifiers) / len(real_identifiers)

        # Определяем стиль именования
        snake = sum(1 for id in meaningful if '_' in id and id.islower())
        camel = sum(1 for id in meaningful if id[0].islower() and any(c.isupper() for c in id) and '_' not in id)
        pascal = sum(1 for id in meaningful if id[0].isupper() and any(c.islower() for c in id) and '_' not in id)
        upper = sum(1 for id in meaningful if id.isupper() and '_' in id)

        total = snake + camel + pascal + upper
        if total > 0:
            self.stats['naming_consistency'] = max(snake, camel, pascal, upper) / total

    def _analyze_anti_patterns(self):
        """Поиск антипаттернов в коде"""
        # Магические числа (исключая 0, 1, -1)
        magic_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', self.code)
        self.stats['magic_number_count'] = sum(1 for n in magic_numbers
                                               if n not in ['0', '1', '-1', '0.0', '1.0'])

    def _analyze_comments_quality(self):
        """Анализ осмысленности комментариев"""

        # Простые конструкции, которые НЕ требуют комментариев
        trivial_patterns = [
            r'int\s+\w+\s*=\s*0',  # int i = 0
            r'for\s*\(.*\)',  # for цикл
            r'if\s*\(.*\)',  # if условие
            r'i\+\+', r'j--',  # инкременты
            r'return\s+\w+;',  # return
        ]

        # Сложные конструкции, которые ТРЕБУЮТ комментариев
        complex_patterns = [
            r'while\s*\([^)]+\)',  # while (особенно с сложным условием)
            r'recursive',  # рекурсия (по имени функции или вызову)
            r'\b[a-zA-Z_]+\s*\([^)]*\)\s*\{[^}]*\b[a-zA-Z_]+\s*\([^)]*\)',  # рекурсивный вызов
            r'\bbreak\b',  # break (часто непонятно зачем)
            r'\bcontinue\b',  # continue
            r'\bgoto\b',  # goto (всегда требует пояснения)
            r'\b(?:if|while)\s*\([^)]*&&[^)]*\)',  # сложное условие с &&
            r'\b(?:if|while)\s*\([^)]*\|\|[^)]*\)',  # сложное условие с ||
            r'\?.*:',  # тернарный оператор
            r'\b(?:int|float|double)\s*\*',  # указатели
            r'\[.*\]\[.*\]',  # двумерные массивы
        ]

        # Находим строки со сложными конструкциями
        complex_lines = set()
        for pattern in complex_patterns:
            for i, line in enumerate(self.lines):
                if re.search(pattern, line):
                    complex_lines.add(i)

        # Проверяем, есть ли комментарии перед этими строками
        commented_complex = 0
        for line_num in complex_lines:
            # Комментарий на той же строке или на предыдущей
            has_comment = False

            # На той же строке
            if '//' in self.lines[line_num]:
                has_comment = True
            # На предыдущей строке (если не пустая)
            elif line_num > 0 and self.lines[line_num - 1].strip().startswith('//'):
                has_comment = True
            # Через одну строку (если между пустая)
            elif line_num > 1 and not self.lines[line_num - 1].strip() and \
                    self.lines[line_num - 2].strip().startswith('//'):
                has_comment = True

            if has_comment:
                commented_complex += 1

        self.stats['complex_code_commented_ratio'] = commented_complex / max(1, len(complex_lines))

    def _analyze_comment_meaningfulness(self):
        """Анализ осмысленности комментариев"""

        # Бесполезные комментарии (говорят очевидное)
        useless_patterns = [
            r'//\s*счетчик\s*$',  # // счетчик
            r'//\s*переменная\s*$',  # // переменная
            r'//\s*временная\s*$',  # // временная
            r'//\s*for\s*$',  # // for
            r'//\s*if\s*$',  # // if
            r'//\s*начало\s*$',  # // начало
            r'//\s*конец\s*$',  # // конец
            r'//\s*условие\s*$',  # // условие
            r'//\s*цикл\s*$',  # // цикл
            r'//\s*\d+\s*$',  # // 123
        ]

        # Полезные комментарии (объясняют почему)
        useful_patterns = [
            r'//\s*потому что',  # // потому что
            r'//\s*так как',  # // так как
            r'//\s*чтобы',  # // чтобы
            r'//\s*иначе',  # // иначе
            r'//\s*если',  # // если (в смысле объяснения)
            r'//\s*TODO',
            r'//\s*FIXME',
            r'//\s*важно',  # // важно
            r'//\s*внимание',  # // внимание
        ]

        comment_lines = []
        in_multiline = False

        for line in self.lines:
            stripped = line.strip()
            if stripped.startswith('//'):
                comment_lines.append(stripped[2:].strip())
            elif '//' in line:
                comment_lines.append(line.split('//')[1].strip())
            elif '/*' in stripped:
                in_multiline = True
                # Извлекаем текст из многострочного комментария
                comment_lines.append(stripped.strip('/*').strip())
            elif in_multiline:
                if '*/' in stripped:
                    in_multiline = False
                    comment_lines.append(stripped.strip('*/').strip())
                else:
                    comment_lines.append(stripped)

        if not comment_lines:
            self.stats['meaningful_comment_ratio'] = 0
            return

        # Считаем полезные и бесполезные
        useless = 0
        useful = 0

        for comment in comment_lines:
            comment_lower = comment.lower()

            # Проверка на бесполезность
            is_useless = any(re.search(p, comment_lower) for p in useless_patterns)
            # Проверка на полезность
            is_useful = any(re.search(p, comment_lower) for p in useful_patterns)

            # Слишком короткий комментарий (< 10 символов) и не специальный
            if len(comment) < 10 and not is_useful:
                useless += 1
            elif is_useless:
                useless += 1
            elif is_useful or len(comment) > 30:  # Длинные комментарии обычно полезны
                useful += 1

        self.stats['meaningful_comment_ratio'] = useful / max(1, len(comment_lines))
        self.stats['useless_comment_count'] = useless
    def _analyze_formatting(self):
        """Анализ форматирования кода"""
        # Длинные строки
        self.stats['lines_over_80'] = sum(1 for l in self.lines if len(l.rstrip()) > 80)
        self.stats['lines_over_100'] = sum(1 for l in self.lines if len(l.rstrip()) > 100)
        self.stats['lines_over_120'] = sum(1 for l in self.lines if len(l.rstrip()) > 120)

        # Пустые строки внутри функций
        empty_in_func = 0
        in_function = False
        for line in self.lines:
            if line.strip() and not line.strip().startswith('//'):
                if '{' in line and not in_function:
                    in_function = True
                elif '}' in line and in_function:
                    in_function = False
            elif not line.strip() and in_function:
                empty_in_func += 1
        self.stats['empty_lines_inside_functions'] = empty_in_func

    def _compute_metrics(self) -> Dict[str, float]:
        """Вычисление итоговых метрик"""
        return {
            # Базовые метрики
            'total_lines': self.stats['total_lines'],
            'code_lines': self.stats['code_lines'],
            'max_line_length': self.stats['max_line_length'],

            # Комментарии
            'comment_lines': self.stats['comment_lines'],
            'doxygen_lines': self.stats['doxygen_lines'],
            'comment_density': self.stats['comment_density'],

            # Именование
            'meaningful_names_ratio': self.stats['meaningful_names_ratio'],
            'naming_consistency': self.stats.get('naming_consistency', 1.0),
            'avg_identifier_len': self.stats['avg_identifier_len'],
            'naming_similarity_score': self.stats.get('naming_similarity_score', 0.0),
            'too_similar_pairs_ratio': self.stats.get('too_similar_pairs_ratio', 0.0),
            'confusing_pairs_count': self.stats.get('confusing_pairs_count', 0),

            # Антипаттерны
            'magic_number_count': self.stats['magic_number_count'],

            # Форматирование
            'lines_over_80': self.stats['lines_over_80'],
            'lines_over_100': self.stats['lines_over_100'],
            'lines_over_120': self.stats['lines_over_120'],
            'empty_lines_inside_functions': self.stats['empty_lines_inside_functions'],
            # Комментарии (дополнительно)
            'complex_code_commented_ratio': self.stats['complex_code_commented_ratio'],
            'meaningful_comment_ratio': self.stats['meaningful_comment_ratio'],
            'useless_comment_count': self.stats['useless_comment_count'],
        }
