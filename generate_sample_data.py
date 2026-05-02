import openpyxl
import random

workbook = openpyxl.Workbook()
sheet = workbook.active
sheet.title = "Data Restoran"

headers = ['ID', 'Kualitas Servis', 'Harga']
sheet.append(headers)

for cell in sheet[1]:
    cell.font = openpyxl.styles.Font(bold=True)

# Generate 100 data restoran random
random.seed(42) 

for i in range(1, 101):
    id_restoran = i
    kualitas_servis = random.randint(1, 100)
    harga = random.randint(25000, 55000)
    
    sheet.append([id_restoran, kualitas_servis, harga])

sheet.column_dimensions['A'].width = 10
sheet.column_dimensions['B'].width = 18
sheet.column_dimensions['C'].width = 12

workbook.save('restoran.xlsx')

