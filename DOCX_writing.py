import PySimpleGUI as sg
import re
import pandas as pd

def ref_sno(Esca, k, qrate, slab, slab3, dox):
    i = k
    ref = []
    rates = []
    avg = 0
    noo = 0
    for p in range(8, len(dox.columns)):
        cell_value = dox.iloc[i, p]
        if cell_value in ('nan', ''):
            continue
        try:
            if '$#$' in cell_value:
                ss = cell_value.split("$#$")
                nos = ss[-1]
                ref.append(f'{dox.iloc[0, p]} item no. {ss[0]}')
                rates.append(nos)
            else:
                nos = cell_value
                ref.append(dox.iloc[0, p])
                rates.append(nos)
            
            avg += float(nos)
            noo += 1
        except ValueError:
            continue
    
    if noo > 0 and avg > 0:
        avgg = avg / noo
        per = round(((float(qrate) - avgg) / avgg) * 100, 2)
        if float(per) <= slab3:
            dec = 'acceptance of rate.'
        else:
            dec = 'One round of negotiation.' if Esca < slab else 'One round of negotiation.'
        return ref, rates, str(round(avgg, 2)), str(per), dec
    
    return [], [], '0', '0', '0'


def draft(Ref, rates, avg_rate, per, dec, final_draft, Esca, rate1, slab, slab3, doc, name, rr):
    if dec == '0':
        final_draft.loc[len(final_draft)] = [name, '--', '--', '--', '--', '--']
    else:
        avg_rate_str = f'Rs. {avg_rate}.'
        if Esca < slab and float(per) < slab3:
            dec = f'Rates accepted as the quoted rate is less than {slab}% below the advertised rate and is also less than {slab3}% of the LAR rate.'
        elif Esca < slab and float(per) > slab3:
            dec = f'A round of negotiation is required as the quoted rate is less than {slab}% below the advertised rate but exceeds {slab3}% of the LAR rate.'
        elif Esca > slab and float(per) < slab3:
            dec = f'A round of negotiation is required as the quoted rate exceeds the advertised rate by more than {slab}% but remains below {slab3}% of the LAR rate.'
        else:
            dec = f'A round of negotiation is required as the quoted rate exceeds the advertised rate by more than {slab}% and also surpasses {slab3}% of the LAR rate.'
        
        decision = f'It is noticed by TC that quoted rate is in {per}% variation of the average LAR value and {round(Esca, 2)}% variation of the advertised rate. Hence TC recommends {dec}'
        
        for h, rate in enumerate(rates):
            final_draft.loc[len(final_draft)] = [name, rr, Ref[h], f'Rs. {rate}', avg_rate_str, decision]
    
    return final_draft


def main(doca):
    dox = pd.read_excel(doca, index_col=0).applymap(str)
    refgex = re.compile(r'\d+\.\d+')

    slab = sg.popup_get_text('Enter % variation from bid rate, default is 10%', default_text="10")
    slab = float(slab) if slab else 10

    slab3 = sg.popup_get_text('Enter % variation from average rate of references, default is 10%', default_text="10")
    slab3 = float(slab3) if slab3 else 10

    final_draft = pd.DataFrame(columns=['Name_of_item', 'Quoted_Rate', 'References_and_S.no', 'Rates', 'Avg_rate', 'Decision'])

    for i in range(len(dox)):
        if dox.iloc[i, 0].isdigit():
            try:
                Esca = float(dox.iloc[i, 7][:-1])
                unit_rate = float(refgex.search(dox.iloc[i, 5]).group())
                rate1 = str(unit_rate * (1 + Esca / 100))
            except (ValueError, AttributeError):
                continue
            
            rr = dox.iloc[i, 5]
            name = f'For the item "{dox.iloc[i + 1, 0]}", The valid L1 has quoted Rs. {rate1} which is {dox.iloc[i, 7]} variation of the advertised rate.'
            Ref, rates, avg_rate, per, dec = ref_sno(Esca, i, rate1, slab, slab3, dox)
            final_draft = draft(Ref, rates, avg_rate, per, dec, final_draft, Esca, rate1, slab, slab3, dox, name, rr)
        elif dox.iloc[i, 0].lower().startswith('schedule'):
            final_draft.loc[len(final_draft)] = [dox.iloc[i, 0], '**', '**', '**', '**', '**']

    return final_draft
