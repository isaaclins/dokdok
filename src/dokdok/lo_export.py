# Runs *inside* LibreOffice (its embedded Python), installed by render.py into dokdok's private
# LibreOffice profile. Loads a docx, updates indexes (TOC) and fields, exports PDF, exits.
import os
import uno
from com.sun.star.beans import PropertyValue


def _pv(name, value):
    p = PropertyValue(); p.Name = name; p.Value = value; return p


def export_pdf(*_):
    ctx = uno.getComponentContext()
    desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
    src = uno.systemPathToFileUrl(os.environ["DOKDOK_IN"])
    dst = uno.systemPathToFileUrl(os.environ["DOKDOK_OUT"])
    doc = desktop.loadComponentFromURL(src, "_blank", 0, (_pv("Hidden", True),))
    try:
        doc.getTextFields().refresh()
        idx = doc.getDocumentIndexes()
        for i in range(idx.getCount()):
            idx.getByIndex(i).update()
        doc.refresh()
        for i in range(idx.getCount()):     # second pass: page numbers settle after first update
            idx.getByIndex(i).update()
        doc.storeToURL(dst, (_pv("FilterName", "writer_pdf_Export"),))
    finally:
        doc.close(True)
    desktop.terminate()


g_exportedScripts = (export_pdf,)
