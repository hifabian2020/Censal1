from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
import pandas as pd
import os
from datetime import datetime

app = FastAPI()

# Rutas estáticas y templates
#app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/procesar/")
async def procesar(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    tmp1 = f"/tmp/{file1.filename}"
    tmp2 = f"/tmp/{file2.filename}"

    # Guardar archivos temporales
    with open(tmp1, "wb") as f:
        f.write(await file1.read())
    with open(tmp2, "wb") as f:
        f.write(await file2.read())

    # Leer solo la hoja "CENSAL"
    df1 = pd.read_excel(tmp1, sheet_name="CENSAL", engine="pyxlsb")
    df2 = pd.read_excel(tmp2, sheet_name="CENSAL", engine="pyxlsb")

    # Unir
    df_final = pd.concat([df1, df2], ignore_index=True)

    # Nombre con timestamp
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/tmp/POBLACION_{now}.xlsx"

    # Exportar
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df_final.to_excel(writer, index=False, sheet_name="CENSO")
        ws = writer.sheets["CENSO"]
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws.column_dimensions[col_letter].width = max_length + 2

    return FileResponse(output_file, filename=os.path.basename(output_file))
