"""
take in a 2d array and return string of a table table
"""


def table_draw(
    data: list[list[str]],
    corner: str = "+",
    h_line: str = "-",
    v_line: str = "|",
    space: str = " ",
    has_header: bool = True,
):
    """
    Docstring for table_draw

    - data : 2d array of strings - each string is an entry in the table, rows must always be the same length
    - corner : corner character
    - h_line : horizontal line character
    - v_line : vertical line character
    - space : space character
    - has_header : whether the first row is a header - adds an extra NL on the 0th row of the table

    """
    col_count = len(data[0])
    row_count = len(data)
    col_widths = [0] * col_count
    for row in data:
        for i in range(col_count):
            col_widths[i] = max(col_widths[i], len(row[i]) + 1)

    out = ""
    out += line(col_widths, corner, h_line)
    for i, row in enumerate(data):
        out += v_line
        for j in range(col_count):
            out += row[j].ljust(col_widths[j]) + v_line
        out += "\n"
        if has_header and i == 0:
            out += line(col_widths, v_line, space)
        out += line(col_widths, corner, h_line)
    return out


def line(col_widths: list[int], corner: str, h_line: str):
    """
    Docstring for line

    - col_widths: list of column widths
    - corner: corner character
    - h_line: horizontal line character

    implimentation shown in table_draw
    """
    out = corner
    for i in range(len(col_widths)):
        out += h_line * (col_widths[i])
        out += corner
    return out + "\n"
