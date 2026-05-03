import openpyxl
import sys

class FuzzyLog:

    def __init__(self):
        self.servis_params = {
            'rendah': (1, 1, 35, 50),       # (a, b, c, d) untuk trapezoid
            'sedang': (35, 50, 65, 80),
            'tinggi': (65, 80, 100, 100)
        }
        self.harga_params = {
            'murah': (25000, 25000, 35000, 42000),
            'sedang': (35000, 42000, 48000, 55000),
            'mahal': (48000, 55000, 55000, 55000)
        }
        self.kelayakan_params = {
            'tidak_layak': (0, 0, 30, 50),
            'cukup_layak': (30, 50, 70, 90),
            'sangat_layak': (70, 90, 100, 100)
        }
        
        self.rules = self._createRules()
    
    def _createRules(self):
        rules = {
            ('rendah', 'murah'): 'tidak_layak',
            ('rendah', 'sedang'): 'tidak_layak',
            ('rendah', 'mahal'): 'tidak_layak',
            
            ('sedang', 'murah'): 'cukup_layak',
            ('sedang', 'sedang'): 'cukup_layak',
            ('sedang', 'mahal'): 'tidak_layak',
            
            ('tinggi', 'murah'): 'sangat_layak',
            ('tinggi', 'sedang'): 'sangat_layak',
            ('tinggi', 'mahal'): 'cukup_layak',
        }
        return rules
    
    def trapezoid(self, x, a, b, c, d):
        if x <= a or x >= d:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a) if b != a else 1.0
        elif b < x <= c:
            return 1.0
        elif c < x < d:
            return (d - x) / (d - c) if d != c else 1.0
        return 0.0
    
    def fuzzification(self, servis, harga):
        # Fuzzifikasi Kualitas Servis
        servis_fuzzy = {}
        for kategori, params in self.servis_params.items():
            servis_fuzzy[kategori] = self.trapezoid(servis, *params)
        
        # Fuzzifikasi Harga
        harga_fuzzy = {}
        for kategori, params in self.harga_params.items():
            harga_fuzzy[kategori] = self.trapezoid(harga, *params)
        
        return servis_fuzzy, harga_fuzzy
    
    def inference(self, servis_fuzzy, harga_fuzzy):
        output_fuzzy = {
            'tidak_layak': 0.0,
            'cukup_layak': 0.0,
            'sangat_layak': 0.0
        }

        # Terapkan aturan fuzzy
        for (servis_cat, harga_cat), output_cat in self.rules.items():
            # T-Norm: MIN (firing strength)
            firing_strength = min(servis_fuzzy[servis_cat], harga_fuzzy[harga_cat])
            
            # S-Norm: MAX (agregasi)
            output_fuzzy[output_cat] = max(output_fuzzy[output_cat], firing_strength)
        
        return output_fuzzy
    
    def defuzz(self, output_fuzzy, servis, harga):
        # Hitung base score dengan Centroid
        resolution = 0.5
        x_values = []
        y_values = []
        
        x = 0.0
        while x <= 100.0:
            membership_at_x = 0.0
            
            for category, firing_strength in output_fuzzy.items():
                if firing_strength > 0:
                    a, b, c, d = self.kelayakan_params[category]
                    membership_trapezoid = self.trapezoid(x, a, b, c, d)
                    clipped = min(membership_trapezoid, firing_strength)
                    membership_at_x = max(membership_at_x, clipped)
            
            x_values.append(x)
            y_values.append(membership_at_x)
            x += resolution
        
        numerator = sum(x * y for x, y in zip(x_values, y_values))
        denominator = sum(y_values)
        
        if denominator == 0:
            base_score = 0.0
        else:
            base_score = numerator / denominator
        
        # Input Adjustment (±5 poin)
        servis_normalized = servis / 100.0  # 0-1
        harga_normalized = 1.0 - ((harga - 25000) / 30000)  # 1(murah)-0(mahal)
        
        adjustment = (servis_normalized * 2.5) + (harga_normalized * 2.5)
        
        final_score = base_score + adjustment
        
        # Pastikan dalam rentang 0-100
        return max(0.0, min(100.0, final_score))
    
    def read(self, filename):
        workbook = openpyxl.load_workbook(filename)
        sheet = workbook.active
            
        data = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row[0] is not None:
                data.append({
                    'id': int(row[0]),
                    'kualitas_servis': float(row[1]),
                    'harga': float(row[2])
                })
            
        workbook.close()
        return data
            
        
    
    def processRes(self, data):
        results = []
        
        for resto in data:
            # 1. Fuzzification
            servis_fuzzy, harga_fuzzy = self.fuzzification(
                resto['kualitas_servis'], 
                resto['harga']
            )
            # 2. Inferensi
            output_fuzzy = self.inference(servis_fuzzy, harga_fuzzy)
            
            # 3. Defuzzification
            skor = self.defuzz(output_fuzzy, resto['kualitas_servis'], resto['harga'])
            
            results.append({
                'id': resto['id'],
                'kualitas_servis': resto['kualitas_servis'],
                'harga': resto['harga'],
                'skor_kelayakan': skor
            })
        
        return results
    
    def select5(self, results):
        sorted_results = sorted(results, key=lambda x: x['skor_kelayakan'], reverse=True)
        return sorted_results[:5]
    
    def save(self, top_5, filename):

            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Top 5 Restoran"

            headers = ['ID Restoran', 'Kualitas Servis', 'Harga', 'Skor Kelayakan']
            sheet.append(headers)

            for cell in sheet[1]:
                cell.font = openpyxl.styles.Font(bold=True)

            for resto in top_5:
                sheet.append([
                    resto['id'],
                    resto['kualitas_servis'],
                    resto['harga'],
                    round(resto['skor_kelayakan'], 2)
                ])

            sheet.column_dimensions['A'].width = 15
            sheet.column_dimensions['B'].width = 18
            sheet.column_dimensions['C'].width = 12
            sheet.column_dimensions['D'].width = 18

            workbook.save(filename)
            workbook.close()
            
            
    
    def display(self, top_5):

        print(f"{'Rank':<6} {'ID':<8} {'Kualitas Servis':<18} {'Harga':<12} {'Skor':<10}")
        print("-"*70)
        
        for i, resto in enumerate(top_5, 1):
            print(f"{i:<6} {resto['id']:<8} {resto['kualitas_servis']:<18.1f} "
                  f"{resto['harga']:<12,.0f} {resto['skor_kelayakan']:<10.2f}")
        


def main():

    input_file = "restoran.xlsx"
    output_file = "peringkat.xlsx"

    fuzzy_system = FuzzyLog()
    data = fuzzy_system.read(input_file)
    results = fuzzy_system.processRes(data)
    top_5 = fuzzy_system.select5(results)
    fuzzy_system.display(top_5)
    
    fuzzy_system.save(top_5, output_file)
    
    print("Test debug")


if __name__ == "__main__":
    main()
