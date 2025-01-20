import re
from collections import defaultdict

from bs4 import BeautifulSoup
from bs4.element import Tag

VARIABLE_PATTERN = re.compile(r'(?<!\\)\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}')
DEFAULT_INDENT = 4


def escape(text):
    return text.replace('`', '\\`')


class JSConvertedElement:
    def __init__(self, lines, varname) -> None:
        self.lines = lines
        self.varname = varname

    def code(self, indent = 0):
        indent_text = ' ' * indent * DEFAULT_INDENT
        return '\n'.join([indent_text+l for l in self.lines])


class AttrHandler:
    def __init__(self, varname) -> None:
        self.varname = varname
        self._handler_map = {
            'class': self.class_,
        }

    def get_handler(self, attr_name):
        return self._handler_map.get(attr_name, self.default)

    def default(self, name, value):
        if value == '':
            value = 'true'
        return f'{self.varname}.setAttribute("{name}", `{escape(value)}`);'

    def class_(self, name, value):
        return f'{self.varname}.className = "{" ".join(value)}";'


class JSCodeFactory:
    @staticmethod
    def createTextNode(varname, text):
        return f'const {varname} = document.createTextNode(`{escape(text)}`);'

    @staticmethod
    def createElement(varname, tag_name):
        return f'const {varname} = document.createElement("{tag_name}");'

    @staticmethod
    def appendChild(varname, child):
        return f'{varname}.appendChild({child});'

    @staticmethod
    def make_function(func_name, converted_element: JSConvertedElement, varnames):
        args_text = ', '.join(varnames)
        return '\n'.join([
            f'function {func_name}({args_text}) ' + '{',
            converted_element.code(indent=1),
            f'{DEFAULT_INDENT*" "}return {converted_element.varname};',
            '}'
        ])


class ElementToJSConverter:
    def __init__(self, html, root_varname = None, varname_attr = None) -> None:
        self.html = html
        self.root_varname = root_varname
        self.varname_attr = varname_attr
        self.variables = []
        self._tag_count = defaultdict(int, {})

    def create_varname(self, tag_name):
        if self.root_varname:
            root_varname = self.root_varname
            self.root_varname = None
            return root_varname
        else:
            self._tag_count[tag_name] += 1
            varname = f'{tag_name}{self._tag_count[tag_name]}'
            while varname in self.variables:
                varname = varname + '_'
            return varname

    def extract_variables_from_text(self, arg):
        if isinstance(arg, str):
            texts = [arg]
        elif isinstance(arg, list):
            texts = arg
        else:
            raise ValueError('Invalid input: expected a string or a list')
        for text in texts:
            vars = VARIABLE_PATTERN.findall(text)
            for var in vars:
                if var not in self.variables:
                    self.variables.append(var)

    def extract_variables(self, element: Tag):
        if isinstance(element, str):
            text = element.strip()
            if not text:
                return
            self.extract_variables_from_text(text)
        elif isinstance(element, Tag):
            varname_attr = self.varname_attr
            if varname_attr and element.has_attr(varname_attr):
                del element.attrs[varname_attr]
            for attr_value in element.attrs.values():
                self.extract_variables_from_text(attr_value)
            for child in element.children:
                self.extract_variables(child)

    def convert_element(self, element):
        lines = []

        if isinstance(element, str):
            text = element.strip()
            if not text:
                return
            varname = self.create_varname('text')
            lines.append(JSCodeFactory.createTextNode(varname, text))

        elif isinstance(element, Tag):
            tag_name = element.name
            varname_attr = self.varname_attr
            if varname_attr and element.has_attr(varname_attr):
                varname = element.attrs.get(varname_attr)
                del element.attrs[varname_attr]
            else:
                varname = self.create_varname(tag_name)

            lines.append(JSCodeFactory.createElement(varname, tag_name))

            attr_handler = AttrHandler(varname)
            for attr_name, attr_value in element.attrs.items():
                handler = attr_handler.get_handler(attr_name)
                lines.append(handler(attr_name, attr_value))

            child_varnames = []
            for child in element.children:
                child_js = self.convert_element(child)
                if not child_js:
                    continue
                lines += child_js.lines
                child_varnames.append(child_js.varname)

            for child_varname in child_varnames:
                lines.append(JSCodeFactory.appendChild(varname, child_varname))

        else:
            raise ValueError(f'Invalid element type {type(element)}')

        return JSConvertedElement(lines, varname)

    def convert(self):
        root_element = BeautifulSoup(self.html, 'html.parser').find()
        self.extract_variables(root_element)
        converted_element = self.convert_element(root_element)
        return converted_element


def convert(html, root_varname = None, indent = 0):
    converter = ElementToJSConverter(html, root_varname)
    return converter.convert().code(indent)


def convert_as_function(html, func_name):
    converter = ElementToJSConverter(html)
    return JSCodeFactory.make_function(
        func_name,
        converter.convert(),
        converter.variables
    )
