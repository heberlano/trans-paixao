from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from xml.sax.saxutils import escape
from operations import money

def report(store):
    b=BytesIO(); doc=SimpleDocTemplate(b,pagesize=A4,rightMargin=38,leftMargin=38,topMargin=38,bottomMargin=42); s=getSampleStyleSheet(); s.add(ParagraphStyle(name='Brand',fontName='Helvetica-Bold',fontSize=23,leading=27,textColor=colors.HexColor('#102B43')))
    m=store.extended(); parts=[Paragraph('TRANSPORTADORA PAIXÃO',s['Brand']),Paragraph('PAIXÃO CONNECT / RELATÓRIO OPERACIONAL',s['Heading2']),Paragraph('Base acadêmica fictícia • Indicadores da sessão atual',s['Normal']),Spacer(1,14)]
    def table(data,widths):
        rows=[[Paragraph(escape(str(x)),s['Normal']) for x in r] for r in data]; t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT'); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#F5A623')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F1F5F9')]),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));return t
    parts += [table([['Indicador','Resultado'],['Cargas',m['total']],['Entregues',m['delivered']],['Em operação',m['active']],['Atrasadas',m['late']],['Protocolos abertos',m['open_tickets']],['Cotações registradas',m['quotes']],['Valor cotado (não receita)',money(m['quoted_total'])],['Satisfação',f"{m['satisfaction']}/5 ({m['ratings']} avaliações)" if m['ratings'] else 'Sem avaliações']],[290,220]),Spacer(1,12),Paragraph('Desempenho por rota',s['Heading2']),table([['Rota','Total','Atrasadas','Taxa']]+[[r['route'].replace('→','>'),r['total'],r['late'],str(r['rate'])+'%'] for r in sorted(m['routes'],key=lambda x:-x['rate'])],[290,65,75,80]),Spacer(1,12),Paragraph('Alertas e ações recomendadas',s['Heading2'])]
    for level,title,action in store.alerts():parts.append(Paragraph(escape(f'{level}: {title}. {action}'),s['Normal']));parts.append(Spacer(1,6))
    def footer(canvas,doc):canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#52677D'));canvas.drawString(38,24,'PACO 2.0 | Uso acadêmico');canvas.drawRightString(557,24,f'Página {doc.page}')
    doc.build(parts,onFirstPage=footer,onLaterPages=footer);return b.getvalue()
