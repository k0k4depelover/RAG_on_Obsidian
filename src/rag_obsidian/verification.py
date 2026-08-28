from walk_vault import walk_vault

if __name__ == "__main__":
    test_vault = "/home/oskar/Desktop/RAG_Obsidian"

    print("Archivos encontrados:")
    for md_file in walk_vault(test_vault, exclude_dirs=[".trash", "templates"]):
        print(f" -> {md_file}")
