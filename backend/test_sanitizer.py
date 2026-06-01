from backend.services.security.data_sanitizer import data_sanitizer

def test():
    # Test text
    text = "Bonjour, je suis le patient Jean Dupont, je suis né le 12/04/1980 et mon email est jean.dupont@email.com. Mon téléphone est le 06 12 34 56 78."
    print("ORIGINAL TEXT:")
    print(text)
    
    sanitized, mapping = data_sanitizer.sanitize(text)
    print("\nSANITIZED TEXT:")
    print(sanitized)
    
    print("\nMAPPING:")
    print(mapping)
    
    restored = data_sanitizer.restore(sanitized, mapping)
    print("\nRESTORED TEXT:")
    print(restored)

    assert text == restored, "Restoration failed!"
    print("\nSUCCESS!")

if __name__ == "__main__":
    test()
