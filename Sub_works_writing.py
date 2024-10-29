import PySimpleGUI as sg
import re
import pandas as pd
import DOCX_writing

def ref_sno(k, qrate, slab, doccuument, refgexs):
    ref = []
    rates = []
    avg = 0
    noo = 0

    for p in range(8, len(doccuument.columns)):
        cell_value = doccuument.iloc[k, p]
        if pd.isna(cell_value):
            continue

        match = refgexs.search(cell_value)
        if match:
            ss = cell_value.split("$#$")
            nos = ss[-1]
            ref.append(f"{doccuument.iloc[0, p]} {ss[0]}")
            rates.append(nos)
            avg += float(nos)
            noo += 1

    if noo > 0:
        avgg = avg / noo
        per = round(((float(qrate) - avgg) / avgg) * 100, 2)
        dec = 'acceptance of rate' if float(per) < slab else 'One round of negotiation'
        return ref, rates, str(round(avgg, 2)), str(per), dec
    else:
        return [], [], '0', '0', '0'

def main_writing(doccuument, final_draft, sheet, refgexs):
    esca_input_text = f"For {sheet}: Enter how much % variation from advertised value is quoted by the contractor including the rebate value"
    esca = sg.popup_get_text(esca_input_text, title="Net Escalation Input", keep_on_top=True) or "0"
    
    slab_input_text = f"For {sheet}: Enter how much % variation from bid rate for each item can be accepted, default is 10%"
    slab = float(sg.popup_get_text(slab_input_text, title="Bid Variation Input", keep_on_top=True) or 10)
    
    lar_input_text = f"For {sheet}: Enter how much % variation from average rate of references for each item can be accepted, default is 10%"
    slab3 = float(sg.popup_get_text(lar_input_text, title="LAR Variation Input", keep_on_top=True) or 10)

    for i in range(len(doccuument) - 1):
        if doccuument.iloc[i, 0].isdigit():
            item_name = f"For the item: {doccuument.iloc[i, 1]}, the valid L1 has quoted"

            try:
                rate1 = refgexs.search(doccuument.iloc[i, 5]).group()
                esca_val = doccuument.iloc[i, 7]
                esca1 = 0
                
                if 'above' in esca_val or 'Above' in esca_val:
                    esca1 = refgexs.search(esca_val).group()
                elif 'below' in esca_val or 'Below' in esca_val:
                    esca1 = '-' + refgexs.search(esca_val).group()
                elif esca_val == 'at par' or esca_val == '':
                    esca1 = 0
                else:
                    esca1 = refgexs.search(esca_val).group()
                    if '-' in esca_val:
                        esca1 = '-' + esca1

                esca1 = float(esca1)
                esca = float(esca1) + float(esca)
                rate1 = str(round(float(rate1) * (1 + esca / 100), 2))
            except:
                continue

            Ref, rates, avg_rate, per, dec = ref_sno(i, rate1, slab3, doccuument, refgexs)
            namw = f"{item_name} Rs.{rate1} which is {round(esca, 2)}% of the advertised rate."
            final_draft = DOCX_writing.draft(Ref, rates, avg_rate, per, dec, final_draft, esca, rate1, slab, slab3, doccuument, namw, rate1)

        else:
            schedule = doccuument.iloc[i, 0]
            final_draft.loc[len(final_draft)] = [schedule, ' __ ', ' __ ', ' __ ', '  __ ', ' __ ']

    return final_draft

def main(doc):
    final_draft = pd.DataFrame(columns=['Name_of_item', 'Quoted_Rate', 'References_and_S.no', 'Rates', 'Avg_rate', 'Decision'])
    refgexs = re.compile(r'\d+\.\d+')

    with pd.ExcelFile(doc) as xls:
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(doc, sheet_name=sheet_name, index_col=0).applymap(str)
            final_draft.loc[len(final_draft)] = ['---', '---', '---', '---', '---', '---']
            final_draft.loc[len(final_draft)] = ['**', '**', '**', '**', '**', '**']
            final_draft.loc[len(final_draft)] = final_draft.columns
            final_draft = main_writing(df, final_draft, sheet_name, refgexs)

    return final_draft
