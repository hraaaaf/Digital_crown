import urllib.request, re, json

def search(q):
    url = f'https://medicament.ma/?choice=specialite&keyword=starts&s={q}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            # Look for <tr class="odd"> or <tr class="even">
            results = []
            
            # This is a bit brittle, but usually the results are in a table row with class row_X
            # A simpler way is to find all rows containing a link to a medicament
            # Example: <td><a href="...">DOLIPRANE 1000 mg</a></td>
            
            # Let's just find all drug names first
            # The structure is usually: <td class="table-name"><a href="https://medicament.ma/medicament/doliprane-1000-mg-2/">DOLIPRANE 1000 mg</a></td>
            matches = re.findall(r'<a href="https://medicament.ma/medicament/[^"]+">([^<]+)</a>', html)
            return matches
            
    except Exception as e:
        print(e)
        return []

print(search("doli"))
