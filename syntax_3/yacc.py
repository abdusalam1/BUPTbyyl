import ply.yacc as yacc
import ply.lex as lex
import sys
from lex import Lexer

filename='comment.pas'

from AST_structure import *



class parser():
    # pascal=Program()
    parse=None
    Symboltable=SymbolTable()
    error=[]

    def child(self):
        def p_programstruct(p):
            'programstruct : program_head SEMICOLON program_body POINT'
            # 语法树节点信息，记录上述产生式下非终结符的节点信息，下同
            p[0] = {
                        "length": len(p),
                        "type": "programstruct",
                         "program_head": p[1],
                         "program_body": p[3],
                        "program": Program(p[1]["id"],p[1]["line"],p[1]["idlist"],p[3])
                    }
            

            # 符号表信息由 program_body 获取
        #    self.Symboltable =p[3]['symbolTable']    

        def p_program_head(p):
            'program_head : PROGRAM ID LPAREN idlist RPAREN '
            p[0] = {
             "id" :p[2],
            "line" :p.lineno(1),
            "idlist":p[4]
             }


            

        def p_program_head_jusi_id(p):
            'program_head :  PROGRAM ID'
            p[0] = {
             "id" :p[2],
            "line" :p.lineno(1),
            "idlist":None
             }
         
        
        def p_program_body(p):
            '''program_body : const_declarations   var_declarations  subprogram_declarations compound_statement'''
            p[0]=SubProgram(p[1],p[2],p[3],p[4])
            # 符号表信息
        #    p[0]['symbolTable']=SymbolTable('program_body',p[1]['constant'],p[2]['Variant'],p[3]['symbol Table'])
       
        def p_empty(p):
            'empty :'
            p[0]=None

        def p_idlist(p):
            '''idlist : ID 
                    | idlist COM ID'''
            if len(p)==2:
                p[0]={p[1]:p.lineno(1)}
            else:
                if p[1].get(p[3])== None : #判断重复
                    p[1][p[3]]=p.lineno(3)
                    p[0]=p[1]
                else:
                    self.error.append({
                        'type':'变量重复',
                        'line':p.lineno(3)
                    })

        def p_const_declerations_empty(p):
            'const_declarations : empty'
            p[0]={
                'constant':p[1]
            }

        def p_const_declerations(p):
            'const_declarations :  CONST const_declaration SEMICOLON'
            #语法树
            p[0]=p[2]
            #符号表
            # p[0]['constant']=p[2]['symbolTable']

        def p_const_decleration(p):
            'const_declaration : ID EQUAL const_value '
            p[0]={
                'constant':[Constant(p[1],p.lineno(1),p[3]['type'],p[3]['value'])]
                }
            #符号表
            # p[0]['symbolTable']={p[1]:Constant(p[1],p.lineno(1),p[3]['type'],p[3]['value'])}
            
        def p_const_decleration_2(p):
            'const_declaration : const_declaration SEMICOLON ID EQUAL const_value'
            cur=Constant(p[3],p.lineno(3),p[5]['type'],p[5]['value'])
            # p[0]=p[1]['constant'].append(cur)
            if p[1] is not None and isinstance(p[1], dict) and 'constant' in p[1]:  
                p[1]['constant'].append(cur)  
                p[0] = p[1]  # 如果 p[0] 需要被设置为更新后的 p[1]  
            else:  
                # 处理错误情况，例如抛出一个异常或者记录一个错误消息  
                raise ValueError("p[1] is None or not a dictionary with 'constant' key")
            #符号表
            # cur={p[3]:Constant(p[1],p.lineno(1),p[3]['type'],p[3]['value'])}
            # if p[1]['symbolTable'].get(p[3])==None:
            #     p[0]['symbolTable']=p[1]['symbolTable'].update(cur)
            # else:
            #     [0]['symbolTable']=p[1]['symbolTable']
            #     self.error.append({
            #             'type':'变量重复',
            #             'line':p.lineno(3)
            #         })
                
        def p_const_value_addop(p):
            '''const_value : ADDOP NUM
                        |    ADDOP DIGITS'''
            p[0]={
                'type':str(type(p[2]))[8:-2],
                'value':p[2] if p[1]=='+' else -p[2]
            }
        def p_const_value_num(p):
            '''const_value :  NUM 
                        |     DIGITS'''
            p[0]={
                'type':str(type(p[1]))[8:-2],
                'value':p[1]
            }

        def p_const_value_letter(p):
            "const_value :  LETTERS "
            p[0]={
                'type':'str',
                'value':p[1]
            }

        #XC


        def p_var_declarations(p):
            'var_declarations : VAR  var_declaration SEMICOLON'
            # 语法树
            p[0] = p[2]
            # 符号表
            # p[0]["Variant"] = p[2]["myVarStruct"]

        def p_var_declarations_empty(p):
            'var_declarations : empty '
             # 语法树
            p[0] = p[1]

        def p_var_declaration(p):
            'var_declaration : idlist COLON type'
            # 语法树
            p[0] = {
                Variant(p[1], p[3]) :p.lineno(1)
            }
            # 符号表
            # p[0]["myVarStruct"] = {"idlist": p[1], "type": p[3]}
            # cursymbol={}

        def p_var_declaration_var(p):
            'var_declaration : var_declaration SEMICOLON idlist COLON type'
            # 语法树
            p[1][Variant(p[3], p[5])]=p.lineno(3)
            p[0] =p[1]
            # 符号表
            # p[0]["myVarStruct"] = {p[1]["myVarStruct"], {"idlist": p[3], "type": p[5]}}

        def p_type(p):
            'type : basic_type '
            p[0]=Type(p[1],p.lineno(1),0,0,0)

        def p_type_array(p):
            'type :  ARRAY LBRACKET period RBRACKET OF basic_type'
            p[0]=Type(p[6],p.lineno(1),1,p[3]['lowerBound'],p[3]['upperBound'])

        def p_basic_type_integer(p):
            'basic_type : INTEGER'
            p[0]=p[1]

        def p_basic_type_real(p):
            'basic_type :  REAL '
            p[0]=p[1]

        def p_basic_type_boolean(p):
            'basic_type : BOOLEAN '
            p[0]=p[1]

        def p_basic_type_char(p):
            'basic_type : CHAR'
            p[0]=p[1]

        def p_period(p):
            'period : DIGITS DOT DIGITS '
            p[0]={
            'lowerBound':[p[1]],
            'upperBound':[p[3]]
        }

        def p_period_2(p):
            'period : period COM DIGITS DOT DIGITS'
            p[0]={
            'lowerBound':p[1]['lowerBound'].append(p[3]),
            'upperBound':p[1]['upperBound'].append(p[5])
        }
            
        def p_subprogram_declarations(p):
            'subprogram_declarations : subprogram_declarations subprogram SEMICOLON '
            # 标志不在子函数中
            self.inSubFun = False
            p[0] = {
                "length": len(p),
                "type": "subprogram_declarations",
                "subprograms": p[1]["subprograms"] + [p[2]]
            }
            # 符号表由产生式右侧生成
            # p[0]["SymbolTable"] = p[1]["SymbolTable"] + [p[2]["SymbolTable"]]

        def p_subprogram_declarations_empty(p):
            'subprogram_declarations : empty '
            p[0] = {
                "length": len(p),
                "type": "subprogram_declarations",
                "subprograms": []
            }
            # p[0]["SymbolTable"] = []

        def p_subprogram(p):
            'subprogram : subprogram_head SEMICOLON subprogram_body'
            p[0] = FucDefn(p[1]['name'],p[1]['lineno'],p[1]['formal'],p[1]['type'],
                       p[3]['con'],p[3]['var'],p[3]['block'])
        # 由产生式右侧构造符号表
            # p[0]["SymbolTable"] = {
            #     "token": p[1]["SymbolTable"]["token"],
            #     "type": p[1]["SymbolTable"]["type"],
            # }

        def p_subprogram_head_procedure(p):
            '''subprogram_head : PROCEDURE ID formal_parameter'''
             # 标识进入子过程
            self.inSubFun = True
            # 重置 subSymbol
            self.subSymbol = {}
            p[0] = {
                'name': p[2],
                'lineno': p.lineno(1),
                'formal': p[3],
                'type': ""
            }
            # 构造符号表
            # p[0]["SymbolTable"] = {
            #     "token": p[2],
            #     "type": None,
            #     "references": p[3]["SymbolTable"]["references"] if p[3] is not None else None,
            #     "variables": p[3]["SymbolTable"]["variables"] if p[3] is not None else None,
            # }
            # 讲子过程加入 subSymbol
            # self.subSymbol = {p[2]: p[0]["SymbolTable"]}
            
        def p_subprogram_head_function(p):
            '''subprogram_head :  FUNCTION ID formal_parameter COLON basic_type'''
            # 标识进入子函数
            self.inSubFun = True
            # 重置 subSymbol
            self.subSymbol = {}
            p[0] = {
                'name': p[2],
                'lineno': p.lineno(1),
                'formal': p[3],
                'type': p[5]
            }
            # p[0]["SymbolTable"] = {
            #     "token": p[2],
            #     "type": p[5]["SymbolTable"],
            #     "references": p[3]["SymbolTable"]["references"] if p[3] is not None else None,
            #     "variables": p[3]["SymbolTable"]["variables"] if p[3] is not None else None,
            # }
            # 将子函数加入 subSymbol
            # self.subSymbol = {p[2]: p[0]["SymbolTable"]}
            # 将各变量加入 subSymbol
            # if p[0]["SymbolTable"]["variables"] is not None:
            #     self.subSymbol = p[0]["SymbolTable"]["variables"]

        def p_formal_parameter(p):
            'formal_parameter : LPAREN parameter_list RPAREN'
            p[0]=p[2]
        

        def p_formal_parameter_empty(p):
            'formal_parameter : empty'
            p[0]=p[1]


        def p_parameter_list(p):
            'parameter_list : parameter'
            para=FormalParameter()
            para.paraId=p[1]["paraId"]
            para.line=p[1]["line"]
            para.type=p[1]["type"]
            # 传值调用,引用调用的区分
            if p[1]["flag"]==True:
                para.flag=True
            p[0]={
                para :p.lineno(1)
            }

        def p_parameter_list_2(p):
            'parameter_list : parameter_list SEMICOLON parameter'
            para=FormalParameter()
            para.paraId=p[3]["paraId"]
            para.line=p[3]["line"]
            para.type=p[3]["type"]
            # 传值调用,引用调用的区分
            if p[1]["flag"]==True:
                para.flag=True
            p[1][para]=p.lineno(3)
            p[0]=p[1]


        def p_parameter(p):
            'parameter : var_parameter'
            p[0]=p[1]

        def p_parameter_value(p):
            'parameter : value_parameter'
            p[1]["flag"]=False
            p[0]=p[1]

        def p_var_parameter(p):
            'var_parameter : VAR value_parameter'
            p[2]["flag"]=True
            p[0]=p[2]

        def p_value_parameter(p):
            'value_parameter : idlist COLON basic_type'
            p[0]={
                "type":p[3],
                "paraId":p[1].keys(),
                "line":p.lineno(2)
                }
            



            # 子程序体
        def p_subprogram_body(p):
            '''subprogram_body : const_declarations var_declarations  compound_statement'''
            p[0] = {
                'con': p[1],
                'var': p[2],
                'block':p[3]
            }
            # p[0]["SymbolTable"] = {
            #     # 常量符号表
            #     "constants": p[1]["SymbolTable"] if p[1] else [],
            #     # 变量符号表
            #     "variables": p[2]["SymbolTable"] if p[2] else [],
            # }
            # 将子函数加入 subSymbol
            # self.subSymbol = p[0]["SymbolTable"]



        def p_compound_statement(p):
            'compound_statement : BEGIN statement_list END'
            p[0] = p[2]

        def p_statement_list(p):
            'statement_list : statement'
            p[0] = [p[1]]

        def p_statement_list_2(p):
            'statement_list :  statement_list SEMICOLON statement'
            p[0] = p[1] + [p[3]] if p[3] else p[1]

        def p_statement_empty(p):
            'statement : empty'
            # 在这里处理空语句的情况
            p[0] = p[1]

        def p_statement_variable_assign(p):
            'statement : variable ASSIGNOP expression'
            # 在这里处理变量赋值语句的情况
            

        def p_statement_func_assign(p):
            'statement : func_id ASSIGNOP expression'
            # 在这里处理函数赋值语句的情况

        def p_func_id(p):
            'func_id : ID'

        def p_statement_procedure_call(p):
            'statement : procedure_call'
            # 在这里处理过程调用语句的情况

        def p_statement_compound(p):
            'statement : compound_statement'
            # 在这里处理复合语句的情况

        def p_statement_if(p):
            'statement : IF expression THEN statement else_part'
            # 在这里处理条件语句的情况

        def p_statement_for(p):
            'statement : FOR ID ASSIGNOP expression TO expression DO statement'
            # 在这里处理for循环语句的情况

        def p_statement_read(p):
            'statement : READ LPAREN variable_list RPAREN'
            # 在这里处理读取语句的情况

        def p_statement_write(p):
            'statement : WRITE LPAREN expression_list RPAREN'
            # 在这里处理写入语句的情况
            
        def p_variable_list_single(p):
            'variable_list : variable'
            # 在这里处理只有一个变量的情况

        def p_variable_list_multiple(p):
            'variable_list : variable_list COM variable'
            # 在这里处理多个变量的情况


        def p_variable(p):
            'variable : ID id_varpart'

        def p_id_varpart_empty(p):
            'id_varpart : empty'
            # 在这里处理空的情况

        def p_id_varpart_with_indices(p):
            'id_varpart : LBRACKET expression_list RBRACKET'
            # 在这里处理带有索引的情况

        def p_procedure_call_no_args(p):
            'procedure_call : ID'
            # 在这里处理没有参数的过程调用情况

        def p_procedure_call_with_args(p):
            'procedure_call : ID LPAREN expression_list RPAREN'
            # 在这里处理带有参数的过程调用情况



        def p_else_part(p):
            'else_part : ELSE statement'

        def p_else_part_empty(p):
            'else_part : empty '

        def p_expression_list_single(p):
            'expression_list : expression'
            # 在这里处理只有一个表达式的情况

        def p_expression_list_multiple(p):
            'expression_list : expression_list COM expression'
            # 在这里处理多个表达式的情况


        def p_expression_simple(p):
            'expression : simple_expression'
            # 在这里处理单一简单表达式的情况

        def p_expression_with_relational_op(p):
            '''expression : simple_expression relop simple_expression
                            '''
            # 在这里处理带有关系运算符的表达式情况
        def p_relop(p):
            '''relop : RELOP 
                    | EQUAL'''

        def p_simple_expression_single_term(p):
            'simple_expression : term'
            # 在这里处理只有一个项的情况

        def p_simple_expression_with_addop(p):
            'simple_expression : simple_expression ADDOP term'
            # 在这里处理带有加法运算符的表达式情况


        def p_term_single_factor(p):
            'term : factor'
            # 处理只有一个因子的情况

        def p_term_with_mulop(p):
            'term : term MULOP factor'
            # 处理带有乘法运算符的表达式情况


        def p_factor_num(p):
            '''factor : NUM
                    | DIGITS'''
            # 处理数字的情况

        def p_factor_variable(p):
            'factor : variable'
            # 处理变量的情况

        def p_factor_expression(p):
            'factor : LPAREN expression RPAREN'
            # 处理表达式的情况

        def p_factor_function_call(p):
            'factor : ID LPAREN expression_list RPAREN'
            # 处理函数调用的情况

        def p_factor_not(p):
            'factor : NOT factor'
            # 处理NOT运算符的情况

        def p_factor_addop(p):
            'factor : ADDOP factor'
            # 处理一元运算符的情况

            
        # 错误处理
        # def p_error(p):
        #     print("语法错误")
        def p_error(p):
            raise yacc.YaccError("语法错误在第 %d 行，第 %d 列 %s" % (p.lineno, p.lexpos,p))

        self.parse=yacc.yacc()

# 建立语法分析器




s=''' program example; {fdthj}
var x, y: integer;
function gcd(a, b: integer): integer;
begin 
if b=0 then gcd:=a
else gcd:=gcd(b, a mod b)
end;
begin
read(x, y);
write(gcd(x, y))
end. '''


class ProgramPrinter:
    def print_program_details(self, program):
        print("Program Details:")
        print(f"Program ID: {program.programId}")
        print(f"Line Number: {program.line}")
        print("Parameter Dictionary:")
        for para_id, line_num in program.paraDict.items():
            print(f"  {para_id}: {line_num}")

        print("SubProgram Details:")
        self.print_subprogram_details(program.subProgram)

    def print_subprogram_details(self, subprogram):
        print(type(subprogram))
        print("Constant List:")
        for const_details in subprogram.constList["constant"]:
            # print(f"  {const_id}:")
            print(f"    - Constant ID: {const_details.constId}")
            print(f"    - Line Number: {const_details.line}")
            print(f"    - Type: {const_details.type}")
            print(f"    - Value: {const_details.Value}\n")

        print("Variable List:")
        for var_details,var_id in subprogram.varList.items():
            print(f"  {var_id}:")
            print(f"    - ID List: {var_details.idlist}")
            print(f"    - Type: {var_details.type.type}")

        print("SubDefinition List:")
        print(f"   length:".format(subprogram.subDefList["length"]))
        print(f"   type:".format(subprogram.subDefList["type"]))
        for funcdef in subprogram.subDefList["subprograms"]:
            self.print_SubDef(funcdef)
      
        print("Block:")
        self.print_statements(subprogram.block.statements)
    
    
    def print_SubDef(self,funcdef):
            print(f"  {funcdef}:")
            print(f"  -funcId:{funcdef.funcId}")
            print(f"  -line:{funcdef.line}")
            print(f"  -formal:")
            self.print_formal_para(funcdef.formalParaList)
            print(f"  -type:{funcdef.type}")

            print("Constant List:")
            if funcdef.constList["constant"] is not None:
                for const_details in funcdef.constList["constant"]:
                    # print(f"  {const_id}:")
                    print(f"    - Constant ID: {const_details.constId}")
                    print(f"    - Line Number: {const_details.line}")
                    print(f"    - Type: {const_details.type}")
                    print(f"    - Value: {const_details.Value}\n")

            print("Variable List:")
            for var_details,var_id in funcdef.varList.items():
                print(f"  {var_id}:")
                print(f"    - ID List: {var_details.idlist}")
                print(f"    - Type: {var_details.type.type}")

            print(f"  block:".format(funcdef.block))

    
    def print_formal_para(self,paralist):
        for para_detail,line_num in paralist.items():
            print(f"    line:{line_num}")
            print(f"    -paraId:{para_detail.paraId}")
            print(f"    -line:{para_detail.line}")
            print(f"    -type:{para_detail.type}")
            print(f"    -flag:{para_detail.flag}\n")

    def print_statements(self, statements):
        for statement in statements:
            if isinstance(statement, Assign):
                print("Assignment:")
                print(f"  Left-hand Side Variable: {statement.varRef.varId}")
                print("  Right-hand Side Expression:")
                self.print_expression(statement.exp)
            elif isinstance(statement, If):
                print("If Statement:")
                print("  Condition:")
                self.print_expression(statement.condition)
                print("  Then Clause:")
                self.print_statements([statement.then])
                print("  Else Clause:")
                self.print_statements([statement.els])
            elif isinstance(statement, While):
                print("While Loop:")
                print("  Condition:")
                self.print_expression(statement.condition)
                print("  Do:")
                self.print_statements([statement.do])
            # Add other statement types as needed

    def print_expression(self, expression):
        print(f"  Type: {expression.type}")
        if expression.type == "var":
            print(f"  Variable Reference: {expression.varRef.varId}")
        elif expression.type == "int":
            print(f"  Integer Value: {expression.intNum}")
        elif expression.type == "real":
            print(f"  Real Value: {expression.realNum}")
        # Add handling for other expression types as needed



#parser = yacc.yacc()
if __name__ == '__main__':
     lexi=Lexer()
     lexi.build(filename)
     tokens=lexi.token
     pp=parser()
     pp.child()

     filename=sys.argv[1] if len(sys.argv) > 1 else 'comment.pas'
    # 打开一个文件  
     file = open(filename, "r")  
    
    # 读取文件内容  
     content = file.read()
     result = pp.parse.parse(content)
     print(result)
     
     #输出注释，可通过成员变量COMMENT访问
    #  print(f"{'COMMENT':^20}") if lexi.COMMENT!={} else print('无注释')
     for key,value in lexi.COMMENT.items():
           print(f'line:{key[0]!s:<5} column:{key[1]!s:<5} value:{value!s:<10}')
     printer = ProgramPrinter()
    #  my_program = Program("program1", 10, {"param1": 20, "param2": 30}, SubProgram({}, {}, {}, []))
    # 假设有一个名为 my_program 的 Program 实例
     printer.print_program_details(result["program"])













        # 参数列表
        # def p_formal_parameter(p):
        #     'formal_parameter : LPAREN parameter_list RPAREN'
        #     p[0] = p[2]
        #     # p[0]["SymbolTable"] = {
        #     #     "references": p[2]["SymbolTable"]["references"],
        #     #     "variables": p[2]["SymbolTable"]["variables"],
        #     # }

        # def p_formal_parameter_empty(p):
        #     'formal_parameter : empty'
        #     p[0] = p[1]

        # # 参数总和
        # def p_parameter_list(p):
        #     'parameter_list : parameter'
        #     p[0] = p[1]          # p[0]是一个dict
        #     # p[0]["SymbolTable"] = {
        #     #     "references": p[1]["SymbolTable"]["references"],
        #     #     "variables": p[1]["SymbolTable"]["variables"],
        #     # }

        # def p_parameter_list_2(p):
        #     'parameter_list : parameter_list SEMICOLON parameter'
        #     p[0] = p[1].update(p[3])
        #     # 符号表从产生式右侧获取
        #     # p[0]["SymbolTable"] = {
        #     #     "references": p[1]["SymbolTable"]["references"] + p[3]["SymbolTable"]["references"],
        #     #     "variables": p[1]["SymbolTable"]["variables"] + p[3]["SymbolTable"]["variables"],
        #     # }

        # # 各个参数，分为传参和传引用
        # def p_parameter(p):
        #     'parameter : var_parameter'
        #     p[0] = {p[1][0]:FormalParameter(p[1].append(True))}
        #     # p[0]["SymbolTable"] = p[1]["SymbolTable"]

        # def p_parameter_value(p):
        #     'parameter : value_parameter'
        #     p[0] = {p[1][0]:FormalParameter(p[1].append(False))}
        #     # 符号表从产生式右侧获取
        #     # p[0]["SymbolTable"] = p[1]["SymbolTable"]

        # def p_var_parameter(p):
        #     'var_parameter : VAR value_parameter'
        #     p[0] = p[2]
        #     # p[0]["SymbolTable"] = {
        #     #     # 函数定义变量是引用调用
        #     #     "references": True,
        #     #     "variables": p[2]["SymbolTable"]["variables"],
        #     # }  
        #     # 规约value_parameter的符号表
        # def p_value_parameter(p):
        #     'value_parameter : idlist COLON basic_type'
        #     p[0] = [p[1],p.lineno(1),p[3]]
        #     # p[0]["SymbolTable"] = {
        #     #     # 函数定义变量不是引用调用
        #     #     "references": False,
        #     #     "variables": []
        #     # }  # value_parameter的符号表
        #     # for key,value in p[1].items():  # 遍历idlist中的每个id, 扩充符号表的变量列表
        #         # p[0]["SymbolTable"]["variables"] = p[0]["SymbolTable"]["variables"] + [{
        #         #     "token": key,
        #         #     "type": p[3]["SymbolTable"],
        #         # }]
