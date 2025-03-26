import sys
from bs4 import BeautifulSoup
import json

from data.input_files.programs_div import HTML_CONTENT

# Map degree types to a letter.
DEGREE_MAPPING = {
    "BACHILLER": "B",
    "BACHILLERATO": "B",
    "MAESTRIA": "M",
    "DOCTORADO": "P",
}


def purify_programs():
    # Extract the JSON from the desired div attribute and manually escape newlines.
    soup = BeautifulSoup(HTML_CONTENT, "html.parser")
    div = soup.find(
        "div", {"class": "form-maker-row ui_pane_row uiw-h-panel-container"}
    )
    json_data = json.loads(div["form-maker-row-properties-json"].replace("\n", "\\n"))

    # Extract the 'option_conf' field, which contains the program details.
    programs_raw = json_data["option_conf"].split("\n")

    # Initialize a list to store parsed data.
    program_list = []

    # Loop through each program entry, skipping the first line.
    for program in programs_raw[1:]:
        # Split the code and program name.
        code_and_name = program.split(" - ", 1)

        if len(code_and_name) == 2:
            code = code_and_name[0].strip()[:4]
            full_name = code_and_name[1].strip().split(" EN ", 1)
            degree_type_raw, program_name = full_name[0], full_name[1]

            # Determine the degree type.
            degree_type = DEGREE_MAPPING.get(degree_type_raw, "N")

            # Append to the list.
            program_list.append(
                {"code": code, "degree_type": degree_type, "program_name": program_name}
            )
    return program_list


def main():
    # Print code, degree type, and program name for each program.
    with open("data/input_files/programs.txt", "w", encoding="UTF-8") as file:
        file.write("Code, Degree Type, Program Name\n")
        program_list = purify_programs()
        for program in program_list:
            file.write(
                program.get("code")
                + ", "
                + program.get("degree_type")
                + ", "
                + program.get("program_name")
                + "\n"
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user. Exiting...")
        sys.exit(0)
