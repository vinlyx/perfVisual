#!/usr/bin/env python3

###### Import Modules
import sys
import os
import base64

###### Document Decription
""" 将SQLite数据库嵌入到HTML可视化文件中 """

###### Version and Date
PROG_VERSION = '0.1.0'
PROG_DATE = '2025-03-31'

###### Usage
USAGE = """

     Version %s  by Vincent Li  %s

     Usage: %s <visual.html> <db.sqlite> >STDOUT
""" % (PROG_VERSION, PROG_DATE, os.path.basename(sys.argv[0]))

######## Global Variable


#######################################################################
############################  BEGIN Class  ############################
#######################################################################


##########################################################################
############################  BEGIN Function  ############################
##########################################################################

def encode_db_to_base64(db_path):
    """将SQLite数据库文件编码为base64字符串"""
    with open(db_path, 'rb') as f:
        db_bytes = f.read()
    return base64.b64encode(db_bytes).decode('utf-8')

def process_html_template(html_path, db_base64, db_prefix, output_path):
    """处理HTML模板，替换embedDB和embedFn变量"""
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 替换embedDB和embedFn变量
    new_content = html_content.replace('let embedDB = null;', f'let embedDB = "{db_base64}";')
    new_content = new_content.replace('let embedFn = null;', f'let embedFn = "{db_prefix}";')

    # 写入新文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

######################################################################
############################  BEGIN Main  ############################
######################################################################
#################################
##
##   Main function of program.
##
#################################
def main():

    ######################### Phrase parameters #########################
    import argparse
    ArgParser = argparse.ArgumentParser(usage=USAGE)
    ArgParser.add_argument("--version", action="version", version=PROG_VERSION)

    (params, args) = ArgParser.parse_known_args()

    if len(args) != 2:
        ArgParser.print_help()
        print("\n[ERROR]: The parameters number is not correct!", file=sys.stderr)
        sys.exit(1)
    else:
        (htmlTmpl, sqlDB) = args # pylint: disable=unbalanced-tuple-unpacking

    ############################# Main Body #############################
    try:
        # 编码数据库为base64
        db_base64 = encode_db_to_base64(sqlDB)

        # 获取数据库文件名前缀
        db_base = os.path.basename(sqlDB)
        db_prefix = db_base.split('_')[0]
        output_path = f"{db_prefix}_visual.html"

        # 处理HTML模板并生成新文件
        process_html_template(htmlTmpl, db_base64, db_base, output_path)

        print(f"Successfully generated: {output_path}")
        return 0

    except Exception as e:
        print(f"[ERROR]: {str(e)}", file=sys.stderr)
        return 1

#################################
##
##   Start the main program.
##
#################################
if __name__ == '__main__':
    return_code = main()
    sys.exit(return_code)

################## God's in his heaven, All's right with the world. ##################