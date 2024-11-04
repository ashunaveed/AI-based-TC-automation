import camelot
import PySimpleGUI as sg
import re
import datetime
import pandas as pd
import rate_restrictions
from llama_cpp import Llama
import textdistance
import os, gc, datetime
from collections import Counter
class ParagraphComparer:
    def __init__(self, model_path):
        self.model = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=int(os.cpu_count()),
            n_gpu_layers=-1
        )
        self.model.verbose = False
        self.para1_prepared = False
        self.para1 = ""
        self.paras = []
        self.system_message = "You are a highly analytical and reasoning agent. You are being asked questions for comparing the detailed meaning of two paras. Respond only with one word, either 'yes' or 'no'. If you cannot arrive at any conclusion, respond with 'no'."

        # Expanded tree-based question sets
        self.questions_tree = {
            "root": {
                "question": "Do the paras 'para1' AND 'para2' refer to the same general object or concept?",
                "yes": "functionality_check",
                "no": "end_no"
            },
            "functionality_check": {
                "question": "Do the paras 'para1' AND 'para2' describe the same functionality or purpose?",
                "yes": "structure_check",
                "no": "end_no"
            },
            "structure_check": {
                "question": "Are the structural aspects of the object described similarly in both paras where paragraph1 is 'para1' AND paragraph2 is 'para2'?",
                "yes": "features_check",
                "no": "detail_discrepancy_check"
            },
            "features_check": {
                "question": "Are the physical characteristics or features of the object described similarly in paras 'para1' AND 'para2'?",
                "yes": "context_check",
                "no": "detail_discrepancy_check"
            },
            "context_check": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Do the paras describe the object in the same context or setting?",
                "yes": "terminology_check",
                "no": "detail_discrepancy_check"
            },
            "terminology_check": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Do the paras use similar terminology to describe the object?",
                "yes": "detail_level_check",
                "no": "discrepancy_check"
            },
            "detail_level_check": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Does one paragraph provide significantly more or different details than the other?",
                "yes": "overall_impression_check",
                "no": "discrepancy_check"
            },
            "additional_check_1": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Do these two paragraphs cover the same timeframe?",
                "yes": "additional_check_2",
                "no": "discrepancy_check"
            },
            "additional_check_2": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Is the tone consistent between both the paragraphs?",
                "yes": "additional_check_3",
                "no": "detail_discrepancy_check"
            },
            "additional_check_3": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Do the paras address the same object and subject type?",
                "yes": "additional_check_4",
                "no": "discrepancy_check"
            },
            "additional_check_4": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Are the descriptions equally detailed in both paras?",
                "yes": "role_complement_check",
                "no": "end_no"
            },
            "role_complement_check": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Are the described functions or roles of the object in the paras complementary?",
                "yes": "end_yes",
                "no": "end_no"
            },
            "detail_discrepancy_check": {
                "question": "Is there a significant discrepancy in the details provided by 'para1' and 'para2'?",
                "yes": "end_no",
                "no": "end_yes"
            },
            "end_yes": "yes",
            "end_no": "no"
        }

        # Add more questions in sub_items_tree and single_sub_items_tree
        self.sub_items_tree = {
            "root": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Do the paras describe the same main work and refer to the same exclusive object?",
                "yes": "discrepancy_check",
                "no": "additional_check_1"
            },
            "discrepancy_check": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Are there any discrepancies that suggest the paras do not refer to the same exclusive object?",
                "yes": "end_no",
                "no": "overall_impression_check"
            },
            "additional_check_1": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Do both paragraphs suggest a similar importance level?",
                "yes": "additional_check_2",
                "no": "end_no"
            },
            "additional_check_2": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Is the narrative style similar between the paragraphs'?",
                "yes": "overall_impression_check",
                "no": "end_no"
            },
            "overall_impression_check": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Do the paras create the same overall impression of the exclusive object?",
                "yes": "end_yes",
                "no": "end_no"
            },
            "end_yes": "yes",
            "end_no": "no"
        }

        self.single_sub_items_tree = {
            "root": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Do the paras describe the same object and use the same terminology?",
                "yes": "detailed_check",
                "no": "end_no"
            },
            "detailed_check": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Does one paragraph provide significantly more or different details about the object than the other?",
                "yes": "discrepancy_check",
                "no": "overall_impression_check"
            },
            "discrepancy_check": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Are there any discrepancies that suggest the paragraphs do not refer to the same object?",
                "yes": "end_no",
                "no": "additional_check_1"
            },
            "additional_check_1": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Is the tone of description in both paras comparable?",
                "yes": "additional_check_2",
                "no": "end_no"
            },
            "additional_check_2": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Are both descriptions neutral and unbiased?",
                "yes": "overall_impression_check",
                "no": "end_no"
            },
            "overall_impression_check": {
                "question": "You are given two paras, where paragraph1 is 'para1' and paragraph2 is 'para2', Do the paragraphs create the same overall impression of the same exclusive object?",
                "yes": "end_yes",
                "no": "end_no"
            },
            "end_yes": "yes",
            "end_no": "no"
        }

    def prepare_para1(self, para1):
        """Prepare any processing related to para1."""
        self.para1 = para1
        self.para1_prepared = True
        self.paras.append(self.para1)

    def compare_with_para2(self, para2):
        """Compare para1 with the given para2."""
        if not self.para1_prepared:
            raise Exception("para1 is not prepared. Call prepare_para1 first.")
        
        self.para2 = para2

        main_item_type = ['For the main work of', 'containing only the work of', 'with only exclusive part of']
        only_item_type = ['For the main work of', 'containing only the exclusive work of']

        if all(ext in self.para1 for ext in main_item_type):
            if all(ezt in self.para2 for ezt in main_item_type):
                result = self._traverse_questions(self.sub_items_tree)
            elif all(ezt in self.para2 for ezt in only_item_type):
                result = self._traverse_questions(self.single_sub_items_tree)
        else:
            result = self._traverse_questions(self.questions_tree)
        
        return result

    def _traverse_questions(self, tree, current_node="root"):
        """Traverse the question tree based on model responses, returning yes if at least 50% of responses are yes."""
        yes_count = 0
        total_questions = 0
        
        while current_node not in ["end_yes", "end_no"]:
            node = tree[current_node]
            question = node["question"].replace('para1', self.para1).replace('para2', self.para2)
            answer = self._ask_question(question)
            
            # Count 'yes' responses and total questions asked
            yes_count += 1 if answer else 0
            total_questions += 1

            current_node = node["yes"] if answer else node["no"]
        
        # Check if yes responses meet or exceed 50% of total questions
        return yes_count > total_questions / 2

    def _ask_question(self, question):
        """Ask a single question to the model, limiting response to 50 characters."""
        try:
            completion = self.model.create_chat_completion(
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": question}
                ], max_tokens=25
            )
            answer = completion['choices'][0]['message']['content'][:50].lower()  # Limit to 50 characters
            return 'yes' in answer.lower()
        except Exception as e:
            print(f"Error during model inference: {e}")
            return False

    def model_delete(self):
        del self.model
        gc.collect()

def remove_duplicates(dataframe):
    for i in range(len(dataframe)):
        first_cell=dataframe.iloc[i,0]
        for j in range(1,len(dataframe.columns)):
            if(dataframe.iloc[i,j]==first_cell):
                dataframe.iloc[i,j]=''
    return dataframe
def remove_duplicates1(dataframe):
    for i in range(len(dataframe)):
        first_cell=dataframe.iloc[i,1]
        for j in range(2,len(dataframe.columns)):
            if(dataframe.iloc[i,j]==first_cell):
                dataframe.iloc[i,j]=''
    return dataframe

def get_index(x,sttring,index, comparer,use_AI):
    '''
    This function takes two inputs, a dataframe and a string1 and matches each string in the 
    dataframe to the given string1 and returns the indes of the string that gets the highest
    match with the string1 and the value of match %.
    '''
    limit = 0.7
    matcho=[]
    required_list = []
    main_item=''
    item= ''
    direction_of_search=0
    #print('Entered get index function')
    for i in range(len(x)):
        if(x.iloc[i,0].isdigit()):
            if(index==2):
                distance_a = 1-textdistance.Cosine(qval=2).normalized_distance(x.iloc[i,index], sttring)
                if(direction_of_search==0):
                    distance_main_item = 1-textdistance.Cosine(qval=2).normalized_distance(x.iloc[i,index], x.iloc[i+1,index])
                    direction_of_search =1
                else:
                    distance_main_item = 1-textdistance.Cosine(qval=2).normalized_distance(x.iloc[i,index], x.iloc[i-1,index])
                if(distance_main_item<0.75):
                    main_item=''
                if(len(main_item)>1 and len(item)>0):
                    required= 'For the main work of '+item+' containing only the work of '+main_item +' with only exclusive part of '+x.iloc[i,index]
                elif(len(main_item)<=1 and len(item)>0):
                    required= 'For the main work '+item+' containing only the exclusive work of '+x.iloc[i,index]
                elif(len(main_item)>1 and len(item)<=0):
                    required = 'For the main work '+main_item+' containing only the exclusive work of '+x.iloc[i,index]
                else:
                    required = x.iloc[i,index]
                distance_b = 1-textdistance.Cosine(qval=2).normalized_distance(required, sttring)
                distance_1 = max(distance_a,distance_b)
                if(distance_a>distance_b):
                    required_list.append(x.iloc[i,index])
                else:
                    required_list.append(required)
            else:
                required=x.iloc[i,index]
                required_list.append(required)
                distance_1 = 1-textdistance.Cosine(qval=2).normalized_distance(required_list[-1], sttring)
            if(distance_1<limit):
                distance_1=0
            matcho.append(distance_1)
        elif('item' in x.iloc[i,0].lower()):
            item= x.iloc[i,1]
            main_item = ''
            direction_of_search=0
            if('schedule' in item.lower() and len(item)<17+len('schedule')):
                # maximum that can be written is 'supply and installation'
                item=''
            required_list.append(0)
            matcho.append(0)
        elif('schedule' in x.iloc[i,0].lower()):
            schedule = x.iloc[i,1]
            required_list.append(0)
            matcho.append(0)
        elif(x.iloc[i,0]==x.iloc[i,1] and x.iloc[i,0]==x.iloc[i,3] and main_item!=x.iloc[i,2]):
            main_item = x.iloc[i,2]
            direction_of_search=0
            required_list.append(0)
            matcho.append(0)
        else:
            required_list.append(0)
            matcho.append(0)
    if(use_AI==0):
        ii = matcho.index(max(matcho))
        return [ii,max(matcho)]
    if(max(matcho)<0.95):
        comparer.prepare_para1(sttring)
        for i in range(len(matcho)):
            if(matcho[i]>limit):
                required=required_list[i]
                if(len(required)<0.3*len(sttring) or len(sttring)<0.3*len(required) or len(required)<10 or len(sttring)<10):
                    pass
                else:
                    result = comparer.compare_with_para2(required)
                if(result):
                    matcho[i]=1
                    break
    ii = matcho.index(max(matcho))
    return [ii,max(matcho)]
def get_index2(x,sttring, comparer, use_AI):
    '''
    This function takes two inputs, a dataframe and a string1 and matches each string in the 
    dataframe to the given string1 and returns the index of the string that gets the highest
    match with the string1 and the value of match %. This is used for comparing PO.
    '''
    limit = 0.7
    matcho=[]
    for i in range(1, len(x)-2):
        if(x.iloc[i,0].isdigit() and len(sttring)>=0.4*len(x.iloc[i+1,0]) and len(x.iloc[i+1,0])>=0.4*len(sttring)):
            required=x.iloc[i+1,0]
            distance_1 = 1-textdistance.Cosine(qval=2).normalized_distance(required, sttring)
            if(distance_1<limit):
                distance_1=0
            matcho.append(distance_1)
            if(distance_1>=0.99):
                break
        else:
            matcho.append(0)
    if(use_AI==0):
        ii = matcho.index(max(matcho))
        return [ii,max(matcho)]
    if(max(matcho)<0.95):
        comparer.prepare_para1(sttring)
        for i in range(len(matcho)):
            if(matcho[i]>limit):
                required = x.iloc[i+1,0]
                result = comparer.compare_with_para2(required)
                if(result):
                    matcho[i]=1
                    break
    ii = matcho.index(max(matcho))
    return [ii,max(matcho)]
def rate_comp(x,index):
    '''
    This fn aim is to return the quoted bid rate from the dataframe given. It 
    takes a dataframe and an index of it as input, sees whether the quotation is as a value, a 
    percentage, on the whole schedule etc and returns the rate.
    '''
    zz = re.compile('\d+.\d+')
    pattern = r"\b[A-Za-z]+"

    # Find all matches
    ss = ' '.join(re.findall(pattern, x.iloc[index,9])).lower()
    if('Above'== ss):
        per = 1+float(zz.search(x.iloc[index,8]).group())/100
    elif('Below'== ss):
        per = 1-float(zz.search(x.iloc[index,8]).group())/100
    elif(x.iloc[index,8]==x.iloc[index,9]):
        rate = zz.search(x.iloc[index,8]).group()
        return rate
    else:
        per =1
    rate = round(float(per*float(zz.search(x.iloc[index,5]).group())),2)
    return str(rate)
def rate_comp1(x,index,rate):
    '''
    This fn aim is to return the quoted bid rate from the dataframe given. It 
    takes a dataframe and an index of it as input, sees whether the quotation is as a value, a 
    percentage, on the whole schedule etc and returns the rate. This fn gets called for a 
    subwork/two table schedule etc.
    '''
    zz = re.compile('\d+.\d+')
    pattern = r"\b[A-Za-z]+"
    try:
        ss = ' '.join(re.findall(pattern, x.iloc[index,9])).lower()
    except:
        ss = None
    # if(ss == None or ss==''):
    #     ss = ' '.join(re.findall(pattern, x.iloc[index+1,9])).lower()
    #     ###print('Ss = ',ss)
    #     index+=1
    if('above'== ss):
        per = 1+float(zz.search(x.iloc[index,8]).group())/100
    elif('below'== ss):
        per = 1-float(zz.search(x.iloc[index,8]).group())/100
    elif('at' == ss or 'atpar'== ss or 'at par'== ss):
        per = 1
    else:
        return 'Tender per is done schedulewise'
    rate = round(float(per*float(rate)),2)
    return str(rate)
def rebate(x,rate):
    zz = re.compile('\d+.\d+')
    for k in range(len(x)-1,0,-1):
        if(any('rebate' in str(item).lower() for item in x.iloc[k])):
            rate1 = float(rate)*(1-float(zz.search(x.iloc[k,-1]).group())/100)
            break
        else:
            rate1=rate
    return str(round(rate1,2))
def Schedules_at(items):
    l = []
    for i in range(len(items)-1):
        if(items.iloc[i,0]=='Schedule'):
            l.append([items.iloc[i,1],i])
    return l        
def Schedules_at1(items):
    l = []
    for i in range(len(items)):
        if('Schedule ' in items.iloc[i,0]):
            l.append([items.iloc[i,0],i])
    return l    
def items_at1(items):
    l = []
    for i in range(len(items)):
        if('item' in items.iloc[i,0].lower()):
            l.append([items.iloc[i,1],i])
    return l
def same_strings(string1, string2):
    zz= re.compile('\w+')
    string1 = zz.search(string1).group()
    string2 = zz.search(string2).group()
    if(string1==string2):
        return True
    return False
def main_df_writing(L1tab, ww, Schedule_name, rate, matchoa,k,item_s_no, name1):
    print('Started writing to excel sheet')
    L1tab.loc[k,ww]= str(Schedule_name +' S.no. '+item_s_no+'.'+' $#$ '+matchoa+' $#$ '+rate)
    L1tab.loc[k+1,ww]= str(name1+' $#$ '+str(matchoa.split(' $#$ ')[0]))
    print('Written one item to excel sheet')
    return L1tab    
def single_schedule(x,zz, index, schedules_single_at, rate1):
    try:
        Schedule_name = schedules_single_at[-1][0]
        cell = x.iloc[index,8]
        pattern = r"\b[A-Za-z]+"
        try:
            try:
                Essca = zz.search(x.iloc[index, 6]).group()
            except:
                Essca =' '.join(re.findall(pattern, x.iloc[index,6])).lower() 
        except:
            Essca = ''
        for d in range(len(schedules_single_at)-1):
            if(index>schedules_single_at[d][-1] and index<schedules_single_at[d+1][-1]):
                Schedule_name = schedules_single_at[d][0]
                indexax = schedules_single_at[d][-1]
                break
        if(cell!='nan' and len(x.columns)==11):
            rate = rate_comp(x,index)
        elif(cell!='nan' and len(x.columns)==10):
            rate = zz.search(cell).group()
        elif(cell=='nan'):
            ratea = zz.search(x.iloc[index,5]).group().replace(',','')
            if(Essca =='' or Essca == 'at par' or Essca==None):
                rate = ratea
            elif('-' in x.iloc[index,6]):
                rate = str(float(ratea)*(1-float(Essca)/100))
            else:
                rate = str(float(ratea)*(1+float(Essca)/100))
            if(x.iloc[index,6]=='At Par'):
                for p in range(len(x)-1,0,-1):
                    if('Total Value' == x.iloc[p,0]):
                        zzs = rate
                        rate = rate_comp1(x, p, rate)
                        if(rate == 'Tender per is done schedulewise'):
                            rate = zzs
                            rate = rate_comp1(x, indexax, rate)
                            break
                        else:
                            pass
        else:
            rate = zz.search(x.iloc[index,8]).group()
        rate = rebate(x,rate)
    except:
        print('Found error comparing\n', L1tab.iloc[k+1,0] ,'\nat schedule level with\n',name)
        return 0,0
    return Schedule_name, rate
def Rates_comparision(L1tab,LOA_names_dates,LOA_ref,comparer,use_AI):
    L1tab = L1tab.applymap(str)
    for i in range(len(LOA_names_dates)):
        print('Started with ', LOA_names_dates[i], ' at ',datetime.datetime.now())
        try:
            ww =len(L1tab.columns)
            L1tab.loc[0,ww]=LOA_names_dates[i]
            x = LOA_ref[i][0]
            any_restriction = LOA_ref[i][-1] 
            L1tab.loc[1,ww] = any_restriction
            if(len(LOA_ref[i])>2):
                tt= True
                schedules = LOA_ref[i][0].copy(deep = True).applymap(str)
                items = LOA_ref[i][1].copy(deep = True).applymap(str)
                schedules_single_at =Schedules_at1(schedules)
                items_at = items_at1(items)
            else:
                tt = False
                x =remove_duplicates(x).applymap(str)
                schedules_single_at1 =Schedules_at1(x)
            zz = re.compile('\d+.\d+')
            for k in range(len(L1tab)):
                if tt:
                    try:
                        if(L1tab.iloc[k,0].isdigit()):# getting error in this
                            item = L1tab.iloc[k,0]
                            item2 = L1tab.iloc[k+1,0]
                            try:
                                if(len(item2.split(' '))<2):
                                    continue
                            except:
                                pass
                            try:
                                schedule = scheduleb 
                                eligebility = rate_restrictions.item_restriction(item, schedule, any_restriction, comparer,use_AI)
                                if(eligebility):
                                    continue
                                else:
                                    pass
                            except:
                                pass
                            index,matchoa = get_index(items,L1tab.iloc[k+1,0],2, comparer, use_AI)
                            index1, matchob = get_index(schedules, L1tab.iloc[k+1,0],1, comparer,use_AI)
                            if(items.iloc[index,2]==''):
                                continue
                            if(matchoa==0 and matchob==0):
                                continue
                            elif(matchoa>=matchob):
                                name='S.no '+items.iloc[index,1]+' '+items.iloc[index,2]
                                try:
                                    rate = zz.search(items.iloc[index,5]).group().replace(',','')
                                except:
                                    continue
                                itea = items_at[-1][0]
                                for d in range(len(items_at)-1):
                                    if(index>items_at[d][-1] and index<items_at[d+1][-1]):
                                        itea = items_at[d][0]
                                        break
                                for pp in range(len(schedules)-1):
                                    if(schedules.iloc[pp,0].isdigit()):
                                        if((itea in schedules.iloc[pp,1]) or (schedules.iloc[pp,1] in itea)):
                                            index1 = pp
                                            break
                                try:
                                    same_quantity_unita = same_strings(re.sub('[^a-zA-Z]', '', L1tab.iloc[k,2]).lower(), items.iloc[index,3].lower())
                                    matchoa = str(matchoa)+ ' $#$ '+ str(same_quantity_unita)
                                    name=itea
                                    serial_no= items.iloc[index,1]
                                except:
                                    pass
                            elif(matchob>matchoa):
                                try:
                                    same_quantity_unit = same_strings(re.sub('[^a-zA-Z]', '', L1tab.iloc[k,2]).lower(), schedules.iloc[index1,4].lower())
                                    matchoa = str(matchob)+ ' $#$ '+ str(same_quantity_unit)
                                    name= schedules.iloc[index1,1]
                                    serial_no=schedules.iloc[index1,0]
                                except:
                                    pass
                                try:
                                    rate = zz.search(schedules.iloc[index1,5]).group().replace(',','')
                                except:
                                    continue
                            try:
                                Schedule_name, rate = single_schedule(schedules,zz, index1,schedules_single_at,rate)
                                L1tab = main_df_writing(L1tab, ww, Schedule_name, rate, matchoa,k,serial_no,name)
                            except:
                                pass
                        else:
                            scheduleb = L1tab.iloc[k,0]
                    except:
                        print('Found error at item level at item \n', L1tab.iloc[k+1,0] ,'  \n comparing \n',items.iloc[index,2],' \n')
                        continue
                else:
                    if(L1tab.iloc[k,0].isdigit()):
                        serial_no_item = L1tab.iloc[k,0]
                        try:
                            schedule = x
                            eligebility = rate_restrictions.item_restriction(serial_no_item, schedule, any_restriction, comparer, use_AI)
                            if(eligebility):
                                pass
                            else:
                                continue
                        except:
                            pass
                        index, matchha = get_index(x,L1tab.iloc[k+1,0],1,comparer, use_AI)
                        if(index!=0):
                            try:
                                same_quantity_unit = same_strings(re.sub('[^a-zA-Z]', '', L1tab.iloc[k,2]).lower(), x.iloc[index,4].lower())
                                matchha = str(matchha)+ ' $#$ '+ str(same_quantity_unit)
                            except:
                                pass
                            try:
                                rate = zz.search(x.iloc[index,5]).group().replace(',','')
                            except:
                                continue
                            Schedule_name, rate = single_schedule(x,zz,index,schedules_single_at1,rate)
                            L1tab = main_df_writing(L1tab, ww, Schedule_name, rate, matchha,k,x.iloc[index,0], x.iloc[index,1])
                    else:
                        schedulea = L1tab.iloc[k,0]
        except:
            print('Found error in extraction of data from ',LOA_names_dates[i],'\n')
            continue
    return L1tab, comparer
def PO_comparision(PO, L1tab, comparer, use_AI):
    '''
    This function is to compare the contents of bid with available PO dataframe.
    PO dataframe contains columns of PO_number, Description, Rate
    '''
    for i in range(len(PO)):
        ww=len(L1tab.columns) 
        L1tab.loc[0,ww]= 'PO no '+str(PO.iloc[i,0])
        index,similar_value = get_index2(L1tab, PO.iloc[i,1], comparer, use_AI)
        L1tab.loc[index,ww]= PO.iloc[i,2]+' $#$ '+str(similar_value)
        L1tab.loc[index+1,ww]=PO.iloc[i,1]+' $#$ '+str(similar_value)
        print('Written PO number ',i, ' in excel sheet')
    return L1tab, comparer
def LOA_references(L1tab, LOA_reef, PO1,use_AI):
    '''
    This fn initializes the comparision of schedule.
    '''
    if(LOA_reef !='nothing'):
        LOA_file1 = LOA_reef.split(';')
        LOA_files=[]
        Rate_references=[]
        zz = re.compile('\d+.\d+')
        for i in range(len(LOA_file1)):
            if(LOA_file1[i][-4:]=='html' or LOA_file1[i][-3:]=='htm'):
                LOA_files.append(LOA_file1[i])
        Rate_references += LOA_files    
        LOA_names_dates=[]
        LOA_ref=[]
        # To check if only one schedule is to be compared eg. for civil engg works.
        layout = [
            [sg.Text('Please check this button if the work is of civil engineering dept')],
            [sg.Button('Select')]
        ]
        # Create the popup window
        window = sg.Window('Select Button Popup', layout)
        # Event loop to wait for user interaction
        while True:
            event, values = window.read()
            # If the window is closed or the Select button is clicked, break the loop
            if event == sg.WINDOW_CLOSED or event == 'Select':
                break
        window.close()
        # Check if the Select button was clicked
        if event == 'Select':
            Engg = True
        else:
            Engg = False
        # Till here, we checked if the work is of civil engg dept
        for item in Rate_references:
            LOA=pd.read_html(item)
            x= LOA[0].applymap(str)
            rate_restrictions1 = rate_restrictions.overall_restrictions(x)
            LOA1=remove_duplicates(LOA[-2])
            LOAb = ''
            for p in range(5, 10):
                if(('LOA' in x.iloc[p,0].lower() or 'letter' in x.iloc[p,0].lower()) and 'date' in x.iloc[p,1].lower()):
                    LOAb = str(x.iloc[p,0])+' : '+str(x.iloc[p,1])
            if(len(LOAb)>1):
                LOA_names_dates.append(LOAb)
            else:
                LOA_names_dates.append('Not identified')
            if(Engg):
                LOA_ref.append([LOA1,rate_restrictions1])
            elif(len(LOA[-1])>3):
                LOA_ref+=[[LOA1, remove_duplicates1(LOA[-1]), rate_restrictions1]]
            else:
                LOA_ref.append([LOA1, rate_restrictions1])
        widtth=len(L1tab.columns)    
        try:
            if(any('rebate' in str(item).lower() for item in L1tab.iloc[-2])):
                rebate1 = L1tab.iloc[-2,-1]
                rebate = float(zz.search(rebate1).group())
                print('\n\n The rebate offered is ', rebate,'%. \n')
        except:
            rebate = 0
        L1tab.loc[0,widtth] ='Escalation'
        for i in range(len(L1tab)):
            if(L1tab.iloc[i,0]):
                try:
                    if(L1tab.iloc[i,5].lower()=='at par'):
                        if(rebate>=0):
                            L1tab.iloc[i,widtth]='-'+str(rebate)+'%'
                    else:
                        try:
                            x=float(zz.search(L1tab.iloc[i,5]).group())
                            y=float(zz.search(L1tab.iloc[i,3]).group())
                            x1 = float(x*(1-float(rebate)/100))
                            item_esca  = str(float(100*(x1-y)/y))
                            total_esca = round(float(item_esca),2)
                            L1tab.iloc[i,widtth]= str(total_esca)+' %'
                        except:
                            if(L1tab.iloc[i,5]=='' or L1tab.iloc[i,5]=='-'):
                                if(any(x in L1tab.iloc[-3,-2].lower() for x in ['above','below'])):
                                    total1 = zz.search(L1tab.iloc[-3,-2]).group()
                                    if('above' in L1tab.iloc[-3,-2].lower()):
                                        L1tab.iloc[i,widtth] = str(float(total1)-rebate)+' %'
                                    elif('below' in L1tab.iloc[-3,-2].lower()):
                                        L1tab.iloc[i,widtth] = '-'+str(float(total1)+rebate)+' %'
                                else:
                                    for hk in range(i,0,-1):
                                        if(any(x in L1tab.iloc[hk,5].lower() for x in ['above','below', 'at par', 'atpar'])):
                                            poer = zz.search(L1tab.iloc[hk,5]).group()
                                            if('above' in L1tab.iloc[hk,5].lower()):
                                                L1tab.iloc[i,widtth] = str(float(poer)-rebate)+' %'
                                            elif('below' in L1tab.iloc[hk,5].lower()):
                                                L1tab.iloc[i,widtth] = '-'+str(float(poer)+rebate)+' %'
                                            elif('at par' in L1tab.iloc[hk,5].lower()):
                                                L1tab.iloc[i,widtth] = ' '+str(rebate)+' %'
                                            elif('atpar' in L1tab.iloc[hk,5].lower()):
                                                L1tab.iloc[i,widtth] = ' '+str(rebate)+' %'
                                            break
                except:
                    L1tab.loc[i,widtth]=''
                    continue
        L1tab.loc[0,widtth]='Escalation'
        if(PO1!='nothing'):
            PO=PO_select(PO1).applymap(str)
            toime = datetime.datetime.now().strftime('%H:%M:%S')
            teexxt = 'Initial framing of all the POs completed at',toime
            sg.popup(teexxt)   
        if(use_AI==1):
            model_dir = "models"
            model_filename = "Meta-Llama-3.1-8B-Instruct-Q8_0.gguf"
            model_path = os.path.join(model_dir, model_filename)
            comparer = ParagraphComparer(model_path=model_path)
        else:
            comparer = 0
        if isinstance(L1tab, pd.DataFrame):
            Latab, comparer=Rates_comparision(L1tab,LOA_names_dates,LOA_ref,comparer, use_AI)
        if(PO1!='nothing'):
            Final_PO_report, comparer = PO_comparision(PO, Latab, comparer,use_AI)
        else:
            Final_PO_report= Latab.copy(deep=True)
        if(use_AI==1):
            comparer.model_delete()
        return Final_PO_report
    else:
        if(PO1=='nothing'):
            return
        else:
            PO=PO_select(PO1)
            toime = datetime.datetime.now().strftime('%H:%M:%S')
            teexxt = 'Initial framing of all the POs completed at',toime
            sg.popup(teexxt)
            if(use_AI==1):
                model_dir = "models"
                model_filename = "Meta-Llama-3.1-8B-Instruct-Q8_0.gguf"
                model_path = os.path.join(model_dir, model_filename)
                comparer = ParagraphComparer(model_path=model_path)
            else:
                comparer =0
            Final_PO_report, comparer = PO_comparision(PO, L1tab, comparer, use_AI)
            if(use_AI==1):
                comparer.model_delete()
            return Final_PO_report
def item1_search(df,p):
    gst = re.compile('\d{2}\s\%')
    rate = 0
    others=0 
    per1 = '0'
    rooat = re.compile('\d+\.\d+')
    description=''
    for i in range(p,len(df)):
        if('PL'==df.iloc[i,0].split(' ')[0] or 'Other'==df.iloc[i,0].split(' ')[0]):
            if(description==''):
                description = df.iloc[i-6,0].replace('\n',' ').replace('\t',' ').split('Description')
                description = ' '.join(description)
                description = description[2:len(description)]
            x=i
            break
        elif('Description'==df.iloc[i,0].split(' ')[0]):
            try:
                description=df.iloc[i,0].split('Description ',1)[-1]
                description = description.replace('\n',' ').replace('\t',' ')
            except:
                pass
            description = description[2:len(description)]
        elif('Basic'==df.iloc[i,0].split(' ')[0]):
            ratee= df.iloc[i,0].replace('\n',' ').replace('\t',' ').split(':',1)[-1]
            ratee = ratee.replace(',','')
            rate = rooat.search(ratee).group()
            yy=i
    if(float(rate)>0):
        for i in range(yy,x):
            for j in range(len(df.columns)):
                xp= str(df.iloc[i,j]).replace('\n',' ').replace('\t',' ')
                try:
                    if('%'==xp.split(' ')[-1]):
                        try:
                            per1 = gst.search(xp).group()
                            per1 = per1.split(' ')[0]
                            break
                        except:
                            per1 = '18'
                    elif('per'==xp.split(' ')[-2] and 'Unit'==xp.split(' ')[-1]):    
                        xp = xp.replace(',','')
                        try:
                            others = float(rooat.search(xp).group())
                            break
                        except:
                            others=0
                            continue
                except:
                    continue
    rate = round(float((float(rate)+others)*(1+float(per1)/100)),2)                
    return description,str(rate),x
def PO_select(file):
    filea = file.split(';')
    PO=pd.DataFrame(columns=['PO_number','Description','rate'])
    required_files=[]
    for p in range(len(filea)):
        if(filea[p][-3:]=='pdf'):
            required_files.append(filea[p])
    file1=required_files
    for i in range(len(file1)):
        try:
            dfa= camelot.read_pdf(file1[i],pages='1-end',flavor='lattice')
            #print('\nStarted referencing ',i,'th PO file')
        except:
            continue
        PO_number=''
        ss=[]
        for k in range(len(dfa)):
            ss.append(dfa[k].df)
        df=pd.concat(ss, ignore_index=True)
        po_details = re.compile('\s..\d{12} \w+ \d\d-\w+-\d\d')
        try:
            PO_number = po_details.search(df.iloc[0,0]).group()
        except:
            PO_number ='0'
            continue
        g=0
        while(True):
            if(df.iloc[g,0]=='Other Terms and Conditions' or df.iloc[g,0]=='Other Terms & Conditions'):
                break
            elif('PL'==df.iloc[g,0].split(' ')[0]):
                description,rate,p = item1_search(df,g+1)
                description = description.replace('\n',' ').replace('\t',' ')
                PO.loc[len(PO)]=[PO_number,description,rate]
                g=p
            else:
                g=g+1
    return PO
def main(use_AI):
    Schedule_file = sg.popup_get_file("Select a bid file:",file_types=(("HTML Files", ["*.html","*.htm"]),),
        multiple_files=False)
    if Schedule_file:
        checkbox_value = sg.popup_yes_no("Please check this box if this is a bid file after negotiation", "Submit")
        if checkbox_value == "Yes":
            x= 4
        else:
            x=6
    if not Schedule_file:
        sg.popup('No Bid document is selected')
        return
    else:
        Reference_files = sg.popup_get_file(
            "Select the Reference LOA files",
            file_types=(("HTML Files", ["*.html","*.htm"]),),
            multiple_files=True)
        PO1 = sg.popup_get_file(
            'Select the PO reference files',
            file_types=(("PO PDF Files", "*.pdf"),),
            multiple_files=True)
        if (not Reference_files) and (not PO1):
            sg.popup('No file for referencing is selected')
            return
        fg= pd.read_html(Schedule_file)    
        L1tab= fg[x]
        L1tab= remove_duplicates(L1tab)
        if(not PO1):
            PO1 = 'nothing'
        if(not Reference_files):
            Reference_files = 'nothing'
        if(len(L1tab)>2):
            LOA_schedule_and_references = LOA_references(L1tab, Reference_files, PO1,use_AI) 
            toime = datetime.datetime.now().strftime('%H:%M:%S')
            teexxt = 'First part of Scheduling completed at',toime
            sg.popup(teexxt)
    return LOA_schedule_and_references
