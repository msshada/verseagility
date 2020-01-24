"""
PREPARE

Before running train, you need to run prepare.py with the respective task.

Example (in the command line):
> cd to root dir
> conda activate nlp
> python code/prepare.py --do_format --task 1
"""

import spacy
import pandas as pd
import string
import re
import argparse

from sklearn.model_selection import StratifiedShuffleSplit

# Custom functions
import sys
sys.path.append('./code')
import helper as he
import data as dt
import custom as cu

logger = he.get_logger(location=__name__)
class Clean():
    """Text preprocessing and cleaning steps

    SUPPORTED LANGUAGES
    - EN
    - DE
    - IT
    - XX (multi - NER only)

    SUPPORTED MODULES
    - Remove Noise
    Remove formatting and other noise that may be contained in emails or
    other document types.
    - Get Placeholders
    Placeholders for common items such as dates, times, urls but also
    custom customer IDs.
    - Remove Stopwords
    Stopwords can be added by adding a language specific stopword file
    to /assets. Format: "assets/stopwords_<language>.txt".
    - Lemmatize
    """

    def __init__(self, task,
                        min_length=20, #TODO: always load, move to transform
                        inference=False):
        self.task = task
        self.language = cu.params.get('language')
        self.min_length = min_length
        
        # Load data class
        self.dt = dt.Data(task=self.task, inference=inference)

        # Load spacy model
        self.nlp = he.load_spacy_model(language=self.language, disable=['ner','parser','tagger'])
        
        # Create stopword list
        stopwords_active = []
        ## Load names
        try:
            with open(self.dt.fn_lookup['fn_names'], encoding='utf-8') as f:
                names = f.readlines()
            stopwords_active = stopwords_active + names
        except Exception as e:
            logger.info('[WARNING] No names list loaded.')
        
        ## Load stopwords
        try:
            with open(self.dt.fn_lookup['fn_stopwords'], encoding='utf-8') as f:
                stopwords = f.readlines()
            stopwords_active = stopwords_active + stopwords
        except Exception as e:
            logger.info('[WARNING] No stopwords list loaded.')
        logger.info(f'[INFO] Active stopwords list lenght: {len(stopwords_active)}')
        ## Add to Spacy stopword list
        for w in stopwords_active:
            self.nlp.vocab[w.replace('\n','')].is_stop = True
   
    def remove(self, line, 
                rm_email_formatting=False, 
                rm_email_header=False, 
                rm_email_footer=False,
                rm_punctuation=False):
        """Remove content from text"""
    
        # Customer Remove
        line = cu.remove(line)

        if rm_email_formatting:
            line = re.sub(r'<[^>]+>', ' ', line) # Remove HTML tags
            line = re.sub(r'^(.*\.eml)', ' ', line) # remove header for system generated emails

        if rm_email_header:
            #DE/EN
            if self.language == 'en' or self.language == 'de':
                line = re.sub(r'\b(AW|RE|VON|WG|FWD|FW)(\:| )', '', line, flags=re.I)
            #DE
            if self.language == 'de':
                line = re.sub(r'(Sehr geehrte( Damen und Herren.)?.)|hallo.|guten( tag)?.', '', line, flags=re.I)

        if rm_email_footer:
            #EN
            if self.language == 'en':
                line = re.sub(r'\bkind regards.*', '', line, flags=re.I)
            #DE
            if self.language == 'de':
                line = re.sub(r'\b(mit )?(beste|viele|liebe|freundlich\w+)? (gr[u,ü][ß,ss].*)', '', line, flags=re.I)
                line = re.sub(r'\b(besten|herzlichen|lieben) dank.*', '', line, flags=re.I)
                line = re.sub(r'\bvielen dank für ihr verständnis.*', '', line, flags=re.I) 
                line = re.sub(r'\bvielen dank im voraus.*', '', line, flags=re.I) 
                line = re.sub(r'\b(mfg|m\.f\.g) .*','', line, flags=re.I)
                line = re.sub(r'\b(lg) .*','',line, flags=re.I)
                line = re.sub(r'\b(meinem iPhone gesendet) .*','',line, flags=re.I)
                line = re.sub(r'\b(Gesendet mit der (WEB|GMX)) .*','',line, flags=re.I)
                line = re.sub(r'\b(Diese E-Mail wurde von Avast) .*','',line, flags=re.I)

        # Remove remaining characters
        ##NOTE: may break other regex
        if rm_punctuation:
            line = re.sub('['+string.punctuation+']',' ',line)
        
        return line

    def get_placeholder(self, line,
                        rp_generic=False,
                        rp_custom=False,
                        rp_num=False):
        '''Replace text with type specfic placeholders'''
        # Customer placeholders
        line = cu.get_placeholder(line)

        # Generic placeholder
        if rp_generic:
            line = re.sub(r' \+[0-9]+', ' ', line) # remove phone numbers
            line = re.sub(r'0x([a-z]|[0-9])+ ',' PER ',line, re.IGNORECASE) # replace 
            line = re.sub(r'[0-9]{2}[\/.,:][0-9]{2}[\/.,:][0-9]{2,4}', ' PDT ', line) # remove dates and time, replace with placeholder
            line = re.sub(r'([0-9]{2,3}[\.]){3}[0-9]{1,3}',' PIP ',line) # replace ip with placeholder
            line = re.sub(r'[0-9]{1,2}[\/.,:][0-9]{1,2}', ' PTI ', line) # remove only time, replace with placeholder
            line = re.sub(r'[\w\.-]+@[\w\.-]+', ' PEM ', line) # remove emails
            line = re.sub(r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&amp;+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+', ' PUR ', line) # Remove links
            line = re.sub(r'€|\$|(USD)|(EURO)', ' PMO ', line)
        
        # Placeholders for numerics
        if rp_num:
            line = re.sub(r' ([0-9]{4,30}) ',' PNL ', line) # placeholder for long stand alone numbers
            line = re.sub(r' [0-9]{2,3} ',' PNS ', line) # placeholder for short stand alone numbers

        return line

    def tokenize(self, line, lemmatize = False, rm_stopwords = False):
        '''Tokenizer for non DL tasks'''
        if not isinstance(line, str):
            line = str(line)
        
        if lemmatize and rm_stopwords:
            line = ' '.join([t.lemma_ for t in self.nlp(line) if not t.is_stop])
        elif lemmatize:
            line = ' '.join([t.lemma_ for t in self.nlp(line)])
        elif rm_stowords:
            line = ' '.join([t.text for t in self.nlp(line) if not t.is_stop])

        return line
    
    def transform(self, texts, 
                    to_lower            = False,
                    # Remove
                    rm_email_formatting = False, 
                    rm_email_header     = False,
                    rm_email_footer     = False, 
                    rm_punctuation      = False,
                    # Placeholders
                    rp_generic          = False, 
                    rp_num              = False,
                    # Tokenize
                    lemmatize           = False,
                    rm_stopwords        = False,
                    return_token        = False,
                    # Whitespace
                    remove_whitespace   = True
                ):
        """Main run function for cleaning process"""

        if isinstance(texts, str):
            texts = [texts]

        # Convert to series for improved efficiency
        df_texts = pd.Series(texts)

        # Avoid loading errors
        df_texts = df_texts.replace('\t', ' ', regex=True)
        
        # Remove noise
        if any((rm_email_formatting, rm_email_header, 
                    rm_email_footer, rm_punctuation)):
            df_texts = df_texts.apply(lambda x: self.remove(x,
                                            rm_email_formatting =   rm_email_formatting, 
                                            rm_email_header     =   rm_email_header, 
                                            rm_email_footer     =   rm_email_footer,
                                            rm_punctuation      =   rm_punctuation))

        # Replace placeholders
        if any((rp_generic, rp_num)):
            df_texts = df_texts.apply(lambda x: self.get_placeholder(x,
                                                        rp_generic  =   rp_generic,
                                                        rp_num      =   rp_num))

        # Tokenize text
        if any((lemmatize, rm_stopwords, return_token)):
            df_texts = df_texts.apply(self.tokenize,
                                    lemmatize = lemmatize,
                                    rm_stopwords = rm_stopwords)
        # To lower
        if to_lower:
            df_texts = df_texts.apply(str.lower)

        # Remove spacing
        if remove_whitespace:
            df_texts = df_texts.apply(lambda x: " ".join(x.split()))
        
        # Return Tokens
        if return_token:
            return [t.split(' ') for t in df_texts.to_list()]
        else:
            return df_texts.to_list()

    def transform_by_task(self, text):
        # CUTOM FUNCTION
        if cu.tasks.get(str(self.task)).get('type') == 'classification':
            return self.transform(text,
                    rm_email_formatting = True, 
                    rm_email_header     = True,
                    rm_email_footer     = True,
                    rp_generic          = True)[0]
        elif cu.tasks.get(str(self.task)).get('type') == 'ner':
            return text[0]
        elif cu.tasks.get(str(self.task)).get('type') == 'qa':
            return self.transform(text,
                    to_lower            = True,
                    # Remove
                    rm_email_formatting = True, 
                    rm_email_header     = True,
                    rm_email_footer     = True, 
                    rm_punctuation      = True,
                    # Placeholders
                    rp_generic          = True, 
                    rp_num              = True,
                    # Tokenize
                    lemmatize           = True,
                    rm_stopwords        = True,
                    return_token        = True
                )[0]
        else:
            logger.info('[WARNING] No transform by task found.')
            return text[0]

def prepare_classification(task, do_format, train_split, min_cat_occurance, download_source):
    # Get clean object
    cl = Clean(task=task)

    if download_source:
        cl.dt.download(source='datastore')

    # Load data
    if do_format:
        data = cl.dt.process(data_type=cu.params.get('prepare').get('data_type'))
    else:
        data = cl.dt.load('fn_prep')
    logger.info(f'Data Length : {len(data)}')

    # Load text & label field
    text_raw = cu.load_text(data)
    data['label'] = cu.load_label(data, task)
    label_list_raw = data.label.drop_duplicates()
    
    # Clean text
    data['text'] = cl.transform(text_raw,
                    rm_email_formatting = True, 
                    rm_email_header     = True,
                    rm_email_footer     = True,
                    rp_generic          = True)
    
    # Filter by length
    data = he.remove_short(data, 'text', min_length=cl.min_length)
    logger.info(f'Data Length : {len(data)}')

    # Remove duplicates
    data_red = data.drop_duplicates(subset=['text'])
    logger.info(f'Data Length : {len(data_red)}')
    
    # Min class occurance
    data_red = data_red[data_red.groupby('label').label.transform('size') > min_cat_occurance]
    logger.info(f'Data Length : {len(data_red)}')

    data_red = data_red.reset_index(drop=True).copy()

    # Label list
    label_list = data_red.label.drop_duplicates()
    logger.info(f'Excluded labels: {list(set(label_list_raw)-set(label_list))}')

    # Split data
    strf_split = StratifiedShuffleSplit(n_splits = 1, test_size=(1-train_split), random_state=200)
    for train_index, test_index in strf_split.split(data_red, data_red['label']):
        df_cat_train = data_red.loc[train_index]
        df_cat_test = data_red.loc[test_index]
    
    # Save data
    cl.dt.save(data_red, fn = 'fn_clean')
    cl.dt.save(df_cat_train[['text','label']], fn = 'fn_train')
    cl.dt.save(df_cat_test[['text','label']], fn = 'fn_test')
    cl.dt.save(label_list, fn = 'fn_label', header=False)

def prepare_ner(task, do_format=True):
    pass

def prepare_qa(task, do_format, download_source):
    # Get clean object
    cl = Clean(task=task)

    if download_source:
        cl.dt.download(source='datastore')
    
    # Load data
    if do_format:
        data = cl.dt.process(data_type=cu.params.get('prepare').get('data_type'))
    else:
        data = cl.dt.load('fn_prep')
    logger.info(f'Data Length : {len(data)}')

    # Filter relevant question answer pairs
    data = cu.filter_qa(data)
    logger.info(f'Data Length : {len(data)}')

    # Load question & answer fields
    question, answer = cu.load_qa(data)
    
    # Clean text
    data['question_clean'] = cl.transform(question,
                    to_lower            = True,
                    rm_email_formatting = True, 
                    rm_email_header     = True,
                    rm_email_footer     = True, 
                    rm_punctuation      = True,
                    rp_generic          = True, 
                    rp_num              = True,
                    lemmatize           = True,
                    rm_stopwords        = True
                    )
    data['answer_clean'] = cl.transform(answer,
                    to_lower            = True,
                    rm_email_formatting = True, 
                    rm_email_header     = True,
                    rm_email_footer     = True, 
                    rm_punctuation      = True,
                    rp_generic          = True, 
                    rp_num              = True,
                    lemmatize           = True,
                    rm_stopwords        = True
                    )
    # For display
    data['answer_text_clean'] = cl.transform(answer,
                rm_email_formatting = True, 
                rm_email_header     = True,
                rm_email_footer     = True
            )

    # Filter by length
    data = he.remove_short(data, 'question_clean', min_length=cl.min_length)
    logger.info(f'Data Length : {len(data)}')

    # Remove duplicates
    data = data.drop_duplicates(subset=['question_clean'])
    logger.info(f'Data Length : {len(data)}')

    data = data.reset_index(drop=True).copy()

    # Save data
    cl.dt.save(data, fn = 'fn_clean')

def run_prepare(task=1, do_format=False, split=0.9, min_cat_occurance=300,  download_source=False):
    logger.info(f'Running <PREPARE> for task {task}')

    task_type = cu.tasks.get(str(task)).get('type')
    if 'classification' == task_type:
        prepare_classification(task, do_format, split, min_cat_occurance, download_source)
    elif 'ner' == task_type:
        prepare_ner(task, do_format)
    elif 'qa' == task_type:
        prepare_qa(task, do_format, download_source)
    else:
        logger.info('[ERROR] TASK TYPE UNKNOWN. Nothing was processed.')

def run():
    """Run from the command line"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", 
                    default=1,
                    type=int,
                    help="Task where: \
                            -task 1 : classification subcat \
                            -task 2 : classification cat \
                            -task 3 : ner \
                            -task 4 : qa") 
    parser.add_argument('--do_format',
                    action='store_true',
                    help="Avoid reloading and normalizing data")
    parser.add_argument("--split", 
                    default=0.9,
                    type=float,
                    help="Train test split. Dev split is taken from train set.")    
    parser.add_argument("--min_cat_occurance", 
                    default=300,
                    type=int,
                    help="Min occurance required by category.") 
    parser.add_argument("--download_source", 
                    action='store_true')          
    args = parser.parse_args()
    run_prepare(args.task, args.do_format, args.split, args.min_cat_occurance, args.download_source)
        
if __name__ == '__main__':
    run()