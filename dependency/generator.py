def format_to_csv(transactions):
    csv_data = f"Timestamp,Amount\n"
    for t in transactions:
        csv_data += f"{t['timestamp']},{t['amount']}\n"
    return csv_data