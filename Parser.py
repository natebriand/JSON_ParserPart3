import os

# Class to represent types of tokens
class TokenType:
    STRING = 'STRING'
    NUMBER = 'NUMBER'
    FALSE = 'FALSE'
    TRUE = 'TRUE'
    NULL = 'NULL'
    LEFTCURLY = 'LEFTCURLY'
    RIGHTCURLY = 'RIGHTCURLY'
    LEFTSQUARE = 'LEFTSQUARE'
    RIGHTSQUARE = 'RIGHTSQUARE'
    COMMA = 'COMMA'
    COLON = 'COLON'
    EOF = 'EOF'

# Class to represent a token itself, with a type and value
class Token:
    def __init__(self, type_, value=None, line_number=None):
        self.type = type_
        self.value = value
        self.line_number = line_number  # used for error handling

# Class that represents the nodes in the parse tree, each token we will define a node
class Node:
    def __init__(self, label=None, closing_label=None, value_type=None):
        self.label = label
        self.closing_label = closing_label
        self.children = []  # Its children will be JSON keys and values
        self.value_type = value_type

    def add_child(self, child):
        self.children.append(child)

    def print_tree(self, depth=0, output_file=None):
        indent = " " * depth
        label = self.label if self.label else "(none)"
        output_file.write(f"{indent}{label}\n")
        for child in self.children:
            child.print_tree(depth + 4, output_file)
        if self.closing_label:
            output_file.write(f"{indent}{self.closing_label}\n")


# A Class used to extract all the tokens from a txt file of token streams, and parse
# them according to the respectful grammar
class ExtractTokensLexer:
    def __init__(self, fileName):
        self.tokens = []  # storing the tokens we get
        self.get_tokens(fileName)  # calls the function to get the tokens
        self.current_token_index = 0  # index to track the current token within the parser

    # goes line by line calling the token_from_line method to get each token
    def get_tokens(self, file_name):
        with open(file_name, 'r') as input_file:
            for line_number, line in enumerate(input_file, start=1):
                line = line.strip()
                token = self.token_from_line(line, line_number)
                if token is not None:
                    self.tokens.append(token)

    def token_from_line(self, line, line_number):
        # removing <, >, and spaces to manipulate easier
        line = line.strip()
        line = line.lstrip("<")
        line = line.rstrip(">")
        line = line.replace(" ", "")
        # get token type and token value
        split = line.split(",", 1)  # limit split to one, so it doesn't split the comma if it's a value
        token_type = split[0]
        token_value = split[1]
        if token_type in vars(TokenType).values():  # make sure it's a respected type
            return Token(token_type, token_value, line_number)   # return a new token based on the type and value
        else:
            return None
    # gets the next token from the list
    def get_next_token(self):
        if self.current_token_index < len(self.tokens):
            token = self.tokens[self.current_token_index]
            self.current_token_index += 1
            return token
        else:
            # Returns EOF token if no more tokens are left
            return Token(TokenType.EOF)


# class that will parse tokens into a parse tree
class Parser:
    def __init__(self, lexer):
        self.lexer = lexer  # we created a new lexer called ExtractTokensLexer
        self.current_token = None
        self.semantic_error = []
        self.seen_keys = set()

    def get_next_token(self):
        # gets the next token from our txt input of tokens
        self.current_token = self.lexer.get_next_token()

    def eat(self, token_type):
        """Consumes a token if it matches the expected type."""
        # this makes it so if we find a semantic error, we
        # will end the parse tree and print out the error
        if self.semantic_error:
            self.current_token = Token(TokenType.EOF)

        if self.current_token.type == token_type:
            self.get_next_token()

    def parse(self):
        """Starts the parsing process by fetching the first token and
        calling the first grammar rule."""
        self.get_next_token()
        return self.object()


    """START OF PARSING GRAMMAR RULES"""

    def object(self):
        """Parses the object grammar rule: object  → '{' items '}'"""
        if self.current_token.type == TokenType.EOF:
            return None
        node = Node(label="{") # node for the opening of an object
        self.eat(TokenType.LEFTCURLY)
        if self.current_token.type != TokenType.RIGHTCURLY: # if not an end curly brace, must be items in the object
            items = self.contents()
            if items:
                for item in items:
                    node.add_child(item) # call the items function, parsing whats inside the object
        if self.current_token.type == TokenType.RIGHTCURLY:
            self.eat(TokenType.RIGHTCURLY)
            node.closing_label = "}"  # Set closing_label only if '}' is consumed
        return node

    def contents(self):
        """Parses the contents grammar rule: contents → pair (',' pair)*
           Note that the left soft brackets are not part of the grammar, and are not terminals.
           They're only for the purpose of representation"""
        if self.current_token.type == TokenType.EOF:
            return None
        items = []
        pair_nodes = self.pair()  # getting the node that is the pair inside the object (key: value)
        if pair_nodes:
            items.extend(pair_nodes)
        while self.current_token.type == TokenType.COMMA:  # if more commas come after each pair, we keep adding pairs
            self.eat(TokenType.COMMA)                      # this is how we represent kleen-*
            pair_nodes = self.pair()
            if pair_nodes:
                items.extend(pair_nodes)
        return items

    def pair(self):
        """Parses the pair grammar rule: pair → id ':' value"""
        if self.current_token.type == TokenType.EOF:
            return None
        key_label = self.current_token.value

        """implementing Type 2 Error"""
        if len(key_label.replace(" ", "")) == 0:
            self.semantic_error.append(f"Error Type 2 at '{self.current_token.value}': Empty Key")

        """implementing Type 4 Error"""
        if key_label == "true" or key_label == "false":
            self.semantic_error.append(f"Error Type 4 at '{self.current_token.value}': Dictionary Key is a Reserved Word")

        """implementing Type 5 Error"""
        if key_label in self.seen_keys:
            self.semantic_error.append(f"Error Type 5 at '{self.current_token.value}': Duplicate Key")

        self.seen_keys.add(key_label)  # adding the key values to check for duplicates later
        key_node = Node(label=f"{key_label}")
        self.eat(TokenType.STRING)
        self.eat(TokenType.COLON)
        value_node = self.value()  # Every key has a value to go along with it
        return [key_node, value_node] if value_node else [key_node]  # return the pair together

    def value(self):
        """Parses the value grammar rule: value → STRING | NUMBER | 'true' | 'false' | 'null' | object | array"""
        if self.current_token.type == TokenType.EOF:
            return None
        if self.current_token.type == TokenType.STRING:
            label = self.current_token.value

            """implementing Type 7 Error"""
            if label == "true" or label == "false":
                self.semantic_error.append(f"Error Type 7 at '{self.current_token.value}': Reserved Word as String")

            self.eat(TokenType.STRING)
            return Node(label=f"{label}", value_type="STRING")
        elif self.current_token.type == TokenType.NUMBER:
            label = self.current_token.value

            """implementing Type 1 Error"""
            if label.startswith(".") or label.endswith("."):
                self.semantic_error.append(f"Error Type 1 at '{self.current_token.value}': Invalid Decimal Number")

            """implementing Type 3 Error"""
            if label.startswith("0") or label.startswith("+"):
                self.semantic_error.append(f"Error Type 3 at '{self.current_token.value}': Invalid Number")

            self.eat(TokenType.NUMBER)
            return Node(label=f"{label}", value_type="NUMBER")
        elif self.current_token.type == TokenType.TRUE:
            label = self.current_token.value
            self.eat(TokenType.TRUE)
            return Node(label="true", value_type="BOOLEAN")
        elif self.current_token.type == TokenType.FALSE:
            label = self.current_token.value
            self.eat(TokenType.FALSE)
            return Node(label="false", value_type="BOOLEAN")
        elif self.current_token.type == TokenType.NULL:
            label = self.current_token.value
            self.eat(TokenType.NULL)
            return Node(label="null", value_type="NULL")
        elif self.current_token.type == TokenType.LEFTSQUARE:
            return self.list()
        elif self.current_token.type == TokenType.LEFTCURLY:
            return self.object()
        else:
            self.current_token = Token(TokenType.EOF)
            return None

    def list(self):
        """Parses the list grammar rule: list → '[' elements ']'"""
        if self.current_token.type == TokenType.EOF:
            return None
        node = Node(label="[")  # node for the opening and closing of a list
        self.eat(TokenType.LEFTSQUARE)
        if self.current_token.type != TokenType.RIGHTSQUARE:  # if not an end square bracket, must be items in the list
            elements = self.items()
            if elements:
                for element in elements:
                    node.add_child(element)
        if self.current_token.type == TokenType.RIGHTSQUARE:
            self.eat(TokenType.RIGHTSQUARE)
            node.closing_label = "]"  # Set closing_label only if ']' is consumed
        return node

    def items(self):
        """Parses the item grammar rule: item → value (',' value)*"""
        if self.current_token.type == TokenType.EOF:
            return None
        items = []
        item_node = self.value()
        if item_node:
            items.append(item_node)  # we know there's at least one item in the array, this adds it
            first_item_type = item_node.value_type
        while self.current_token.type == TokenType.COMMA:  # loop keeps checking for list items and adding them as
            self.eat(TokenType.COMMA)  # a child of the element node
            item_node = self.value()
            if item_node:

                """implementing Type 6 Error"""
                if item_node.value_type != first_item_type:
                    self.semantic_error.append(f"Error Type 6 at '{item_node.label}': Inconsistent List Element Type")

                items.append(item_node)
        return items

    """END OF PARSING GRAMMAR RULES"""


# function that runs test files through the parser
def run_test_files(input_folder='input_folder', output_folder='output_folder'):
    ''
    """ALL TEST FILES FOR ALL 7 ERROR TYPES"""
    for i in range(1, 8):
        # get names of files, input01.txt, input02.txt, etc
        input_file_name = os.path.join(input_folder, f"Type{i}ErrorInput.txt")
        output_file_name = os.path.join(output_folder, f"Type{i}ErrorOutput.txt")

        lexer = ExtractTokensLexer(input_file_name)  # create lexer to get the tokens
        parser = Parser(lexer)  # parse the tokens

        with open(output_file_name, 'w') as file:
            tree = parser.parse()
            if tree:
                tree.print_tree(output_file=file)  # print parse tree to the file
            if parser.semantic_error:
                file.write("\n")
                file.write(f"{parser.semantic_error[0]}\n")  # if errors, print them to the file


    """3 TEST FILES FOR SEMANTICALLY CORRECT INPUT"""
    for i in range(1, 4):
        # get names of files, input01.txt, input02.txt, etc
        input_file_name = os.path.join(input_folder, f"CorrectInput{i}.txt")
        output_file_name = os.path.join(output_folder, f"CorrectOutput{i}.txt")

        lexer = ExtractTokensLexer(input_file_name)  # create lexer to get the tokens
        parser = Parser(lexer)  # parse the tokens

        with open(output_file_name, 'w') as file:
            tree = parser.parse()
            if tree:
                tree.print_tree(output_file=file)  # print parse tree to the file
            if parser.semantic_error:
                file.write("\n")
                file.write(f"{parser.semantic_error[0]}\n")  # if errors, print them to the file


if __name__ == "__main__":
    run_test_files()
