# -*- coding: utf-8 -*-
"""
Created on Fri Feb 10 07:33:57 2023

@author: PC1
"""
import final_schedule, rate_restrictions   
import re, os
import pandas as pd
import PySimpleGUI as sg
import textdistance
def get_indexa(x,schedule_index,schedule_index_name,index):
    '''
    This function takes two inputs, a dataframe and a string1 and matches each string in the 
    dataframe to the given string1 and returns the indes of the string that gets the highest
    match with the string1 and the value of match %.
    '''
    matcho=[]
    pattern = r'[A-Za-z0-9\.]+'
    for i in range(len(x)):
        if(x.iloc[i,0].isdigit()):
            matches = re.findall(pattern, schedule_index)
            extracted_text = ' '.join(matches)
            matchesb = re.findall(pattern, x.iloc[i,1])
            extracted_text1 = ' '.join(matchesb)
            if(extracted_text==extracted_text1):
                required=x.iloc[i,index]
                matchh=1-textdistance.Cosine(qval=2).normalized_distance(required, schedule_index_name)
                if(matchh<0.7):
                    matchh=0
                matcho.append(matchh)
            else:
                matcho.append(0)
        else:
            matcho.append(0)
    ii = matcho.index(max(matcho))
    return [ii,max(matcho)]
def Rates_comparision(L1tab,LOA_names_dates,LOA_ref, comparer, use_AI,Engg = False):
    L1tab = L1tab.applymap(str)
    restrictions = []
    print('Entered rate restrictions')
    for i in range(len(LOA_names_dates)):
        try:
            ww =len(L1tab.columns)
            if(i ==0):
                ww0 = ww
                columnns = List(L1tab.columns)
            L1tab.loc[0,ww]=LOA_names_dates[i]
            x = LOA_ref[i][0]
            any_restriction = LOA_ref[i][-1]
            print('started with ', LOA_names_dates[i])
            restrictions.append(LOA_ref[i][-1]) 
            if(len(LOA_ref[i])>2):
                tt= True
                schedules = LOA_ref[i][0].copy(deep = True).applymap(str)
                items = LOA_ref[i][1].copy(deep = True).applymap(str)
                schedules_single_at =final_schedule.Schedules_at1(schedules)
                items_at = final_schedule.items_at1(items)
            else:
                tt = False
                x =final_schedule.remove_duplicates(x).applymap(str)
                schedules_single_at1 =final_schedule.Schedules_at1(x)
            zz = re.compile('\d+.\d+')
            escaa =re.compile('\w+\s\w+')
            main_item = ''
            direction_of_search = 0
            for k in range(len(L1tab)):
                if tt:
                    try:
                        if(L1tab.iloc[k,0].isdigit()):# getting error in this
                            item = L1tab.iloc[k,0]
                            if(direction_of_search==0):
                                distance_main_item = 1-textdistance.Cosine(qval=2).normalized_distance(L1tab.iloc[k,2], L1tab.iloc[k+1,2])
                                direction_of_search =1
                            else:
                                distance_main_item = 1-textdistance.Cosine(qval=2).normalized_distance(L1tab.iloc[k,2], L1tab.iloc[k-1,2])
                            if(distance_main_item<0.75):
                                main_item=''
                            if(len(main_item)>1):
                                item_name = 'For the main work of '+main_item+' containing only the exclusive work of '+L1tab.iloc[k,2]
                            else:
                                item_name = L1tab.iloc[k,2]
                                if(item_name==''):
                                    continue
                            try:
                                schedule = scheduleb 
                                eligebility = rate_restrictions.item_restriction(item, schedule, any_restriction, comparer, use_AI)
                                if(eligebility):
                                    continue
                                else:
                                    pass
                            except:
                                pass
                            if(Engg):
                                item_name = L1tab.iloc[k,2]
                                index,matchoa = get_indexa(items,L1tab.iloc[k,1],item_name,2)
                            else:
                                index,matchoa = final_schedule.get_index(items,item_name,2, comparer, use_AI)
                            index1, matchob = final_schedule.get_index(schedules, item_name,1, comparer, use_AI)
                            pattern = r"\b[A-Za-z]+"
                            if(matchoa>matchob):
                                name='S.no '+items.iloc[index,1]+' '+items.iloc[index,2]
                                itea = items_at[-1][0]
                                for d in range(len(items_at)-1):
                                    if(index>items_at[d][-1] and index<items_at[d+1][-1]):
                                        itea = items_at[d][0]
                                        break
                                for pp in range(len(schedules)-1):
                                    if(schedules.iloc[pp,0].isdigit()):
                                        if((itea in schedules.iloc[pp,1]) or (schedules.iloc[pp,1] in itea)):
                                            index_name = pp
                                            break
                                try:
                                    try:
                                        rate = zz.search(items.iloc[index,5]).group().replace(',','')
                                    except:
                                        continue
                                    same_quantity_unita = final_schedule.same_strings(re.sub('[^a-zA-Z]', '', L1tab.iloc[k,3]).lower(), items.iloc[index,3].lower())
                                    matchoa = str(matchoa)+ ' $#$ '+ str(same_quantity_unita)
                                    s_no=items.iloc[index,1]
                                    index1 = index_name
                                    name = items.iloc[index,2]
                                except:
                                    pass
                            elif(matchob>matchoa):
                                try:
                                    same_quantity_unitb = final_schedule.same_strings(re.sub('[^a-zA-Z]', '', L1tab.iloc[k,3]).lower(), schedules.iloc[index1,4].lower())
                                    matchoa = str(matchob)+ ' $#$ '+ str(same_quantity_unitb)
                                    s_no = schedules.iloc[index1,0]
                                    name = schedules.iloc[index1,1]
                                except:
                                    pass
                                try:
                                    rate = zz.search(schedules.iloc[index1,5]).group().replace(',','')
                                except:
                                    continue
                            try:
                                Schedule_name, rate=final_schedule.single_schedule(schedules,zz, index1,schedules_single_at,rate)    
                                L1tab = single_df(Schedule_name, s_no, name, rate, matchoa, k ,ww)
                            except:
                                pass
                        elif(L1tab.iloc[k,0]=='' and L1tab.iloc[k,0]==L1tab.iloc[k,1] and L1tab.iloc[k,0]==L1tab.iloc[k,4] and main_item!=L1tab.iloc[k,2]):
                            main_item = L1tab.iloc[k,2]
                            direction_of_search = 0
                        else:
                            scheduleb = L1tab.iloc[k,0]
                            main_item = ''
                            direction_of_search =0
                    except:
                        continue
                else:
                    if(L1tab.iloc[k,0].isdigit()):
                        serial_no_item = L1tab.iloc[k,0]
                        if(direction_of_search ==0):
                            distance_main_item = 1-textdistance.Cosine(qval=2).normalized_distance(L1tab.iloc[k,2], L1tab.iloc[k+1,2])
                            direction_of_search =1
                        else:
                            distance_main_item = 1-textdistance.Cosine(qval=2).normalized_distance(L1tab.iloc[k,2], L1tab.iloc[k-1,2])
                        if(distance_main_item<0.75):
                            main_item=''
                        if(len(main_item)>1):
                            item_name = 'For the main work of '+main_item+' containing only the exclusive work of '+L1tab.iloc[k,2]
                        else:
                            item_name = L1tab.iloc[k,2]
                        try:
                            schedule = schedulea
                            eligebility = rate_restrictions.item_restriction(serial_no_item, schedule, any_restriction, comparer, use_AI)
                            if(eligebility):
                                continue
                            else:
                                pass
                        except:
                            pass
                        index, matchha = final_schedule.get_index(x,item_name,1,comparer, use_AI)
                        if(index!=0):
                            try:
                                same_quantity_unit = same_strings(re.sub('[^a-zA-Z]', '', L1tab.iloc[k,3]).lower(), x.iloc[index,4].lower())
                                matchha = str(matchha)+ ' $#$ '+ str(same_quantity_unit)
                            except:
                                pass
                            try:
                                rate = zz.search(x.iloc[index,5]).group().replace(',','')
                            except:
                                continue
                            try:
                                Schedule_name, rate = final_schedule.single_schedule(x,zz, index,schedules_single_at,rate)
                                L1tab = single_df(Schedule_name, x.iloc[index,0],x.iloc[index,1],rate,matchha, k,ww)
                            except:
                                pass
                    elif(L1tab.iloc[k,0]=='' and L1tab.iloc[k,0]==L1tab.iloc[k,1] and L1tab.iloc[k,0]==L1tab.iloc[k,4] and main_item!=L1tab.iloc[k,2]):
                        main_item = L1tab.iloc[k,2]
                        direction_of_search =0
                    else:
                        schedulea = L1tab.iloc[k,0]
                        main_item = ''
                        direction_of_search =0
        except:
            print('Found error in ',LOA_names_dates[i],'\n')
            continue
    try:
        restrictions1= ['px' for i in range(len(L1tab)-len(restrictions))]+restrictions
        restrictions2 = pd.DataFrame(restrictions1, columns= L1tab.columns)
        L1tab= pd.concat([L1tab,restrictions2], ignore_index = True)
        print('Connected restrictions to the end of the schedule')
    except:
        L1tab = L1tab
    return L1tab, comparer
def single_df(Schedule_name, s_no, name, rate, motcha, k ,ww):
    L1tab.loc[k,ww]= str(Schedule_name +' S.no. '+s_no + ' $#$ '+motcha+' $#$ '+name+' $#$ '+rate)
    return L1tab
def LOA_references(L1tab, LOA_reef, PO1, use_AI, comparer,Engg):
    '''
    This fn initializes the comparision of schedule.
    '''
    if(LOA_reef !='nothing'):
        Rate_references=LOA_reef.split(';')
        LOA_names_dates=[]
        LOA_ref=[]
        # To check if only one schedule is to be compared eg. for civil engg works.
        # Till here, we checked if the work is of civil engg dept
        for item in Rate_references:
            LOA=pd.read_html(item)
            x= LOA[0].applymap(str)
            rate_restrictions1 = rate_restrictions.overall_restrictions(x)
            LOA1=final_schedule.remove_duplicates(LOA[-2].fillna(' '))
            LOA_names_dates.append(str(x.iloc[8,0])+':'+str(x.iloc[8,1]))
            if(Engg):
                LOA_ref.append([LOA1,rate_restrictions1])
            elif(len(LOA[-1])>=3):
                LOA_ref.append([LOA1, final_schedule.remove_duplicates1(LOA[-1]), rate_restrictions1])
                print('Got LOA references')
            else:
                LOA_ref.append([LOA1, rate_restrictions1])
                print('Got LOA references')
        Final_PO_report, comparer=Rates_comparision(L1tab,LOA_names_dates,LOA_ref, comparer, use_AI,Engg)
        if isinstance(L1tab, pd.DataFrame) and PO1!='nothing':
            PO=final_schedule.PO_select(PO1).applymap(str)
            Final_PO_report, comparer = PO_comparision(PO, Final_PO_report, comparer, use_AI)
    else:
        if(PO1=='nothing'):
            return
        else:
            PO=final_schedule.PO_select(PO1)
            toime = datetime.datetime.now().strftime('%H:%M:%S')
            teexxt = 'Initial framing of all the POs completed at',toime
            sg.popup(teexxt)
            Final_PO_report, comparer = PO_comparision(PO, L1tab, comparer, use_AI)
    return Final_PO_report

def PO_comparision(PO, L1tab, comparer, use_AI):
    '''
    This function is to compare the contents of bid with available PO dataframe.
    PO dataframe contains columns of PO_number, Description, Rate
    '''
    for i in range(1, len(PO)):
        try:
            ww=len(L1tab.columns) 
            L1tab.loc[0,ww]= 'PO no '+str(PO.iloc[i,0])
            index,similar_value = final_schedule.get_index2(L1tab, PO.iloc[i,1], comparer, use_AI)
            L1tab.loc[index,ww]= ' $#$ '+PO.iloc[i,1]+' $#$ '+ str(similar_value)+' $#$ '+ PO.iloc[i,2]
        except:
            pass
    return L1tab, comparer
def main(use_AI):
    number = sg.popup_get_text("Enter the number of subworks involved",
                               title="Number Input", default_text="",
                               keep_on_top=True)
    try:
        number = int(number)
        L1tabs= []
        subwork_Reference_files = []
        PO1s=[]
        final_sub_schedule = []
        Engg = []
        for k in range(number):
            Subworks_file = sg.popup_get_file(
                'Select the '+ str(k+1) +'th subworks bid file',
                file_types=(("HTML Files", "*.html"),),
                multiple_files=False)
            if not Subworks_file:
                continue
            L1= pd.read_html(Subworks_file)[-1].fillna(' ')
            L1 = pd.concat([pd.DataFrame([L1.columns],columns = L1.columns),L1])
            L1.columns = [i for i in range(len(L1.columns))]
            L1tabs.append(final_schedule.remove_duplicates(L1).applymap(str).reset_index(drop=True).copy(deep=True))
            layout = [
            [sg.Text('Please check this button if the work is of civil engineering dept')],
            [sg.Button('Select')]
            ]
            # Create the popup window
            window = sg.Window('Select if Engg', layout)
            # Event loop to wait for user interaction
            while True:
                event, values = window.read()
                # If the window is closed or the Select button is clicked, break the loop
                if event == sg.WINDOW_CLOSED or event == 'Select':
                    break
            if event == 'Select':
                Engg.append(True)
            else:
                Engg.append(False)
            window.close()
            subwork_Reference_file = sg.popup_get_file(
                'Select the '+str(k+1)+'th Reference LOA files',
                file_types=(("HTML Files", "*.html"),),
                multiple_files=True)
            if(not subwork_Reference_file):
                subwork_Reference_file = 'nothing'
            subwork_Reference_files.append(subwork_Reference_file)    
            PO1 = sg.popup_get_file(
                'Select the PO reference files for '+str(k+1)+' th subwork',
                file_types=(("PO PDF Files", "*.pdf"),),
                multiple_files=True)
            if(not PO1):
                PO1 = 'nothing'
            PO1s.append(PO1)
        if(use_AI==1):
            model_dir = "models"
            model_filename = "Meta-Llama-3-8B-Instruct-Q8_0.gguf"
            model_path = os.path.join(model_dir, model_filename)
            comparer = final_schedule.ParagraphComparer(model_path=model_path)
        else:
            comaparer =0
        for i in range(len(L1tabs)):
            try:
                print('Started with ', str(i+1),' referenceing')
                final_sub_schedule.append(LOA_references(L1tabs[i], subwork_Reference_files[i], PO1s[i], use_AI, comaparer,Engg[i]))
                print('Scheduling of Subwork_',str(i+1),' is completed')
            except:
                continue
        if(use_AI==1):
            comparer.model_delete()
        return final_sub_schedule
    except ValueError:
        sg.popup("Invalid input. Please enter a valid number.")
        return 


