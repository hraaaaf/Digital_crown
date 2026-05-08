import sys
import os

print("Checking WeasyPrint...")
try:
    import weasyprint
    print(f"WeasyPrint {weasyprint.__version__} is installed.")
    
    from weasyprint import HTML
    test_path = 'scratch/test_wp.pdf'
    if not os.path.exists('scratch'):
        os.makedirs('scratch')
        
    HTML(string='<h1>Digital Crown Test</h1>').write_pdf(test_path)
    print(f"SUCCESS: PDF rendered at {test_path}")
    
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
except Exception as e:
    print(f"SYSTEM ERROR (GTK+ missing?):")
    print(f"Detail: {type(e).__name__}: {e}")
