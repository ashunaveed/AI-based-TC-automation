import PySimpleGUI as sg
import Sub_works_references
import Sub_works_writing
import DOCX_writing
import final_schedule
import pandas as pd
import datetime
import os
import requests
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows


def apply_format_to_sheet(sheet):
    """Apply formatting to the sheet based on cell content."""
    for row in sheet.iter_rows():
        for cell in row:
            content = cell.value
            if isinstance(content, str) and '$#$' in content:
                parts = content.split('$#$')
                num_value = float(parts[1]) if len(parts) > 2 else float(parts[-1])
                is_italic = parts[2] == 'False' if len(parts) > 2 else False
                cell.fill = get_fill_color(num_value)
                if is_italic:
                    cell.font = Font(underline='single')


def get_fill_color(value):
    """Get the color for cell based on value."""
    if 0.6 <= value < 0.75:
        intensity = int((value - 0.6) * 255 / 0.15)
        return PatternFill(start_color=f"FF{255-intensity:02X}{255-intensity:02X}", end_color=f"FF{255-intensity:02X}{255-intensity:02X}", fill_type="solid")
    elif 0.75 <= value < 0.9:
        intensity = int((value - 0.75) * 255 / 0.15)
        return PatternFill(start_color=f"FFFF{intensity:02X}00", end_color=f"FFFF{intensity:02X}00", fill_type="solid")
    elif 0.9 <= value <= 1:
        intensity = int((value - 0.9) * 255 / 0.1)
        return PatternFill(start_color=f"{(255-intensity):02X}FF{(255-intensity):02X}", end_color=f"{(255-intensity):02X}FF{(255-intensity):02X}", fill_type="solid")
    return None


def create_folder_if_not_exists(folder_name):
    """Create folder if it doesn't exist."""
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
        print(f"Created folder: {folder_name}")


def download_model_if_not_exists(model_url, model_path):
    """Download model if it does not exist locally."""
    if not os.path.exists(model_path):
        response = requests.get(model_url)
        if response.status_code == 200:
            with open(model_path, "wb") as model_file:
                model_file.write(response.content)
            print(f"Model downloaded and saved to {model_path}")
        else:
            print(f"Failed to download the model. Status code: {response.status_code}")


def merge_and_align_cells(workbook, processed_data, path):
    """Merge and align cells in the workbook and save it."""
    sheet = workbook.active
    cols = list(processed_data.columns)
    for col_num, col in enumerate(cols, start=1):
        start_row = None
        for row_num in range(2, sheet.max_row + 2):
            if row_num <= sheet.max_row and sheet.cell(row=row_num, column=col_num).value == sheet.cell(row=row_num-1, column=col_num).value:
                if start_row is None:
                    start_row = row_num - 1
            else:
                if start_row:
                    sheet.merge_cells(start_row=start_row, start_column=col_num, end_row=row_num-1, end_column=col_num)
                    start_row = None
    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    workbook.save(path)


def process_file(work_folders, use_AI, folder_index, function, file_ext):
    """Process file based on event and save the result."""
    try:
        processed_data = function(use_AI)
        timestamp = datetime.datetime.now().strftime('%H_%M_%S of %d-%m')
        temp_file = f"temporary_file_{timestamp}.{file_ext}"
        folder_path = os.path.join(os.getcwd(), work_folders[folder_index])
        output_path = os.path.join(folder_path, temp_file)
        processed_data.to_excel(output_path, engine='openpyxl')
        workbook = load_workbook(output_path)
        for sheet_name in workbook.sheetnames:
            apply_format_to_sheet(workbook[sheet_name])
        final_file = f"final_comparision_file_{timestamp}.{file_ext}"
        workbook.save(os.path.join(folder_path, final_file))
        sg.popup(f'The file {final_file} is generated in {work_folders[folder_index]}')
    except Exception as e:
        sg.popup(f"An error occurred: {e}")


def main():
    work_folders = [
        'main_work_comparision',
        'sub_work_comparision',
        'Main_work_schedule_report',
        'sub_work_schedule_report',
    ]

    for folder in work_folders:
        create_folder_if_not_exists(os.path.join(os.getcwd(), folder))

    model_url = "https://huggingface.co/lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF/raw/main/Meta-Llama-3.1-8B-Instruct-Q8_0.gguf"
    model_dir = "models"
    model_filename = "Meta-Llama-3.1-8B-Instruct-Q8_0.gguf"
    download_model_if_not_exists(model_url, os.path.join(model_dir, model_filename))

    layout = [
        [sg.Checkbox("Use AI", key="-USE_AI-")],
        [sg.Button("Process primary_bid", key="-LOA1-"), sg.Button("Process sub_bid", key="-MIN_LOA-")],
        [sg.Text("Select the main work comparision sheet:"), sg.Input(key="-EXCEL1-"), sg.FileBrowse()],
        [sg.Text("Select the sub work comparision sheet:"), sg.Input(key="-EXCEL2-"), sg.FileBrowse()],
        [sg.Button("Process final main schedule", key="-FINAL_main_work-")],
        [sg.Button("Process final sub schedule", key="-FINAL_sub_work-")],
    ]
    
    window = sg.Window("Tender Rate Comparator", layout)

    while True:
        event, values = window.read()
        use_AI = int(values.get("-USE_AI-", 0))
        if event == sg.WINDOW_CLOSED:
            break
        elif event == "-LOA1-":
            process_file(work_folders, use_AI, 0, final_schedule.main, 'xlsx')
        elif event == "-MIN_LOA-":
            process_file(work_folders, use_AI, 1, Sub_works_references.main, 'xlsx')
        elif event == "-FINAL_main_work-":
            filepath = values["-EXCEL1-"]
            if filepath:
                process_file(work_folders, filepath, 2, DOCX_writing.main, 'xlsx')
        elif event == "-FINAL_sub_work-":
            filepath = values["-EXCEL2-"]
            if filepath:
                process_file(work_folders, filepath, 3, Sub_works_writing.main, 'xlsx')

    window.close()


if __name__ == "__main__":
    main()
