import csv
import io
from typing import List

def format_to_csv(headings: List[str], data: List[List[str]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    
    writer.writerow(headings)
    writer.writerows(data)
    
    return output.getvalue()