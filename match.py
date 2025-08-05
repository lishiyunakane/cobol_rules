import base64
import glob

# with open(txt_input_path, 'r', encoding='utf-8') as f:
#         base85_string = f.read()

#     binary_data = base64.b85decode(base85_string.encode('utf-8'))

#     with open(output_7z_path, 'wb') as f:
#         f.write(binary_data)

#     print(f"已从 {txt_input_path} 还原为 {output_7z_path}")


with open("0805.zip", "wb") as fout:
    for binfile in sorted(glob.glob("./chunk_*.txt")):
        print(binfile)
        with open(binfile, "r", encoding="utf-8") as f:
            base85_string = f.readline().strip()
        binary_data = base64.b85decode(base85_string.encode("utf-8"))
        fout.write(binary_data)
