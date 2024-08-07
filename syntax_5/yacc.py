import ply.yacc as yacc
import ply.lex as lex
import sys
from lex import Lexer

filename = r'comment.pas'

from codeGenerate import *
from AST_structure import *


class parser():
    parse = None
    error = []

    def child(self, name):
        def p_programstruct(p):
            'programstruct : program_head SEMICOLON program_body POINT'
            # 语法树节点信息，记录上述产生式下非终结符的节点信息，下同
            p[0] = {
                "length": len(p),
                "type": "programstruct",
                "program_head": p[1],
                "program_body": p[3],
                "program": Program(p[1]["id"], p[1]["line"], p[1]["idlist"], p[3])
            }

        def p_program_head(p):
            'program_head : PROGRAM ID LPAREN idlist RPAREN '
            p[0] = {
                "id": p[2],
                "line": p.lineno(1),
                "idlist": p[4]
            }
            SymbolTable.append({
                'id': p[2],
                'type': 'main',
                'para': {tuple(p[4].keys()): p.lineno(1)},
                'const': {  # 'id':'type',
                },
                'var': {},
                'subF': {}
            })

        def p_program_head_jusi_id(p):
            'program_head :  PROGRAM ID'
            p[0] = {
                "id": p[2],
                "line": p.lineno(1),
                "idlist": {}
            }
            SymbolTable.append({
                'id': p[2],
                'type': 'main',
                'para': {},
                'const': {  # 'id':'type',
                },
                'var': {},
                'subF': {}
            })

        def p_program_body(p):
            '''program_body : const_declarations   var_declarations  subprogram_declarations compound_statement'''
            p[0] = SubProgram(p[1], p[2], p[3], p[4])
            # 符号表信息

        def p_empty(p):
            'empty :'
            p[0] = None

        def p_idlist(p):
            '''idlist : ID
                    | idlist COM ID'''
            if len(p) == 2:
                p[0] = {p[1]: p.lineno(1)}
            else:
                if p[1].get(p[3]) == None:  # 判断重复
                    p[1][p[3]] = p.lineno(3)
                    p[0] = p[1]
                else:
                    self.error.append({
                        'type': '变量重复',
                        'line': p.lineno(3)
                    })

        def p_const_declerations_empty(p):
            'const_declarations : empty'
            p[0] = {
                'constant': p[1]
            }

        def p_const_declerations(p):
            'const_declarations :  CONST const_declaration SEMICOLON'
            # 语法树
            p[0] = p[2]
            # 符号表

            for i in p[2]['constant']:
                # 声明的const量名与形参名相同
                if SymbolTable[-1]["para"].get(i.constId, "NOT_FOUND") != "NOT_FOUND":
                    self.error.append({
                        'type': '常量名与形参名重复',
                        'line': p.lineno(1)
                    })
                if SymbolTable[-1]["subF"].get(i.constId, "NOT_FOUND") != "NOT_FOUND":
                    self.error.append({
                        'type': '常量名与函数名重复',
                        'line': p.lineno(1)
                    })

            for const in p[2]['constant']:
                if SymbolTable[-1]['const'].get(const.constId) == None:
                    SymbolTable[-1]['const'][const.constId] = const.type
                else:
                    self.error.append({
                        'type': '常量重复',
                        'line': p.lineno(3)
                    })
                # para

        def p_const_decleration(p):
            'const_declaration : ID EQUAL const_value '
            p[0] = {
                "constant": [Constant(p[1], p.lineno(1), p[3]['type'], p[3]['value'])]
            }

        def p_const_decleration_2(p):
            'const_declaration : const_declaration SEMICOLON ID EQUAL const_value'
            cur = Constant(p[3], p.lineno(3), p[5]['type'], p[5]['value'])
            # p[0]=p[1]['constant'].append(cur)
            if p[1] is not None and isinstance(p[1], dict) and 'constant' in p[1]:
                p[1]['constant'].append(cur)
                p[0] = p[1]  # 如果 p[0] 需要被设置为更新后的 p[1]
            else:
                # 处理错误情况，例如抛出一个异常或者记录一个错误消息
                raise ValueError("p[1] is None or not a dictionary with 'constant' key")
            # 符号表
            # cur={p[3]:Constant(p[1],p.lineno(1),p[3]['type'],p[3]['value'])}

        def p_const_value_addop(p):
            '''const_value : ADDOP NUM
                        |    ADDOP DIGITS'''
            p[0] = {
                'type': str(type(p[2]))[8:-2],
                'value': p[2] if p[1] == '+' else -p[2]
            }

        def p_const_value_num(p):
            '''const_value :  NUM
                        |     DIGITS'''
            p[0] = {
                'type': str(type(p[1]))[8:-2],
                'value': p[1]
            }

        def p_const_value_letter(p):
            "const_value :  LETTERS "
            p[0] = {
                'type': 'char',
                'value': p[1]
            }

        def p_const_value_boolean(p):
            '''const_value :  FALSE
                        |     TRUE'''
            p[0] = {
                'type': 'boolean',
                'value': p[1]
            }

        # XC

        def p_var_declarations(p):
            'var_declarations : VAR  var_declaration SEMICOLON'
            # 语法树
            p[0] = p[2]
            # 符号表

            for i in p[2].keys():
                # 声明的变量名与形参名相同
                for id in i.idlist:
                    if SymbolTable[-1]["para"].get(id, "NOT_FOUND") != "NOT_FOUND":
                        self.error.append({
                            'type': '变量名与形参名重复',
                            'line': p.lineno(1)
                        })
                    if SymbolTable[-1]["subF"].get(id, "NOT_FOUND") != "NOT_FOUND":
                        self.error.append({
                            'type': '变量名与函数名重复',
                            'line': p.lineno(1)
                        })
            for const in p[2].keys():
                ty = const.type
                for id in const.idlist:
                    if ty.arrFlag:
                        SymbolTable[-1]['var'][id] = [
                            ty.type + str(ty.arrFlag),
                            ty.lB,
                            ty.uB
                        ]
                    else:
                        SymbolTable[-1]['var'][id] = ty.type

        def p_var_declarations_empty(p):
            'var_declarations : empty '
            # 语法树
            p[0] = p[1]

        def p_var_declaration(p):
            'var_declaration : idlist COLON type'
            # 语法树
            p[0] = {
                Variant(p[1], p[3]): p.lineno(1)
            }
            # 符号表
            # p[0]["myVarStruct"] = {"idlist": p[1], "type": p[3]}
            # cursymbol={}

        def p_var_declaration_var(p):
            'var_declaration : var_declaration SEMICOLON idlist COLON type'
            # 语法树
            p[1][Variant(p[3], p[5])] = p.lineno(3)
            p[0] = p[1]
            # 符号表
            # p[0]["myVarStruct"] = {p[1]["myVarStruct"], {"idlist": p[3], "type": p[5]}}

        def p_type(p):
            'type : basic_type '
            p[0] = Type(p[1], p.lineno(1), 0, 0, 0)

        def p_type_array(p):
            'type :  ARRAY LBRACKET period RBRACKET OF basic_type'
            p[0] = Type(p[6], p.lineno(1), 1, p[3]['lowerBound'], p[3]['upperBound'])

        def p_basic_type_integer(p):
            'basic_type : INTEGER'
            p[0] = 'int'

        def p_basic_type_real(p):
            'basic_type :  REAL '
            p[0] = 'float'

        def p_basic_type_boolean(p):
            'basic_type : BOOLEAN '
            p[0] = 'boolean'

        def p_basic_type_char(p):
            'basic_type : CHAR'
            p[0] = p[1]

        def p_period(p):
            'period : DIGITS DOT DIGITS '
            p[0] = {
                'lowerBound': [p[1]],
                'upperBound': [p[3]]
            }

        def p_period_2(p):
            'period : period COM DIGITS DOT DIGITS'
            p[1]['lowerBound'].append(p[3])
            p[1]['upperBound'].append(p[5])
            p[0] = p[1]

        def p_subprogram_declarations(p):
            'subprogram_declarations : subprogram_declarations subprogram SEMICOLON '
            # 标志不在子函数中
            self.inSubFun = False
            p[0] = {
                "length": len(p[1]["subprograms"]) + 1,
                "type": "subprogram_declarations",
                "subprograms": p[1]["subprograms"] + [p[2]]
            }
            # 符号表由产生式右侧生成
            # p[0]["SymbolTable"] = p[1]["SymbolTable"] + [p[2]["SymbolTable"]]

        def p_subprogram_declarations_empty(p):
            'subprogram_declarations : empty '
            p[0] = {
                "length": 0,
                "type": "subprogram_declarations",
                "subprograms": []
            }
            # p[0]["SymbolTable"] = []

        def p_subprogram(p):
            'subprogram : subprogram_head SEMICOLON subprogram_body'
            p[0] = FucDefn(p[1]['name'], p[1]['lineno'], p[1]['formal'], p[1]['type'],
                           p[3]['con'], p[3]['var'], p[3]['block'])
            if len(SymbolTable) > 1:
                SymbolTable[-2]['subF'][SymbolTable[-1]['id']] = [SymbolTable[-1]['para'], SymbolTable[-1]['type']]
                SymbolTable.pop()

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
                'type': "void"
            }
            # 构造符号表
            par = {}

            for pp in p[3].keys():
                par[tuple(pp.paraId)] = pp.type

            if SymbolTable[-1]['subF'].get(p[2]) == None:
                SymbolTable.append({
                    'id': p[2],
                    'type': 'void',
                    'para': par,
                    'const': {  # 'id':'type',
                    },
                    'var': {},
                    'subF': {}
                })
            else:
                raise ValueError("This function has been already difined")

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
            # 符号表
            par = {}

            for pp in p[3].keys():
                par[tuple(pp.paraId)] = pp.type

            if SymbolTable[-1]['subF'].get(p[2]) == None:
                SymbolTable.append({
                    'id': p[2],
                    'type': p[5],
                    'para': par,
                    'const': {  # 'id':'type',
                    },
                    'var': {},
                    'subF': {}
                })
            else:
                raise ValueError("This function has been already difined")

        def p_formal_parameter(p):
            'formal_parameter : LPAREN parameter_list RPAREN'
            p[0] = p[2]

        def p_formal_parameter_no_args(p):
            'formal_parameter : LPAREN RPAREN'
            p[0] = {}
            pass

        def p_formal_parameter_empty(p):
            'formal_parameter : empty'
            p[0] = {}

        def p_parameter_list(p):
            'parameter_list : parameter'
            para = FormalParameter()
            para.paraId = p[1]["paraId"]
            para.line = p[1]["line"]
            para.type = p[1]["type"]
            # 传值调用,引用调用的区分
            if p[1]["flag"] == True:
                para.flag = True
            p[0] = {
                para: p.lineno(1)
            }

        def p_parameter_list_2(p):
            'parameter_list : parameter_list SEMICOLON parameter'
            para = FormalParameter()
            para.paraId = p[3]["paraId"]
            para.line = p[3]["line"]
            para.type = p[3]["type"]
            # 传值调用,引用调用的区分
            for pp in p[1].keys():
                para.flag = True if pp.flag == True else False
            if p[3]["flag"] == True:
                para.flag = True
            p[1][para] = p.lineno(2)
            p[0] = p[1]

        def p_parameter(p):
            'parameter : var_parameter'
            p[0] = p[1]

        def p_parameter_value(p):
            'parameter : value_parameter'
            p[1]["flag"] = False
            p[0] = p[1]

        def p_var_parameter(p):
            'var_parameter : VAR value_parameter'
            p[2]["flag"] = True
            p[0] = p[2]

        def p_value_parameter(p):
            'value_parameter : idlist COLON basic_type'
            p[0] = {
                "type": p[3],
                "paraId": list(p[1].keys()),
                "line": p.lineno(2)
            }

            # 子程序体

        def p_subprogram_body(p):
            '''subprogram_body : const_declarations var_declarations  compound_statement'''
            p[0] = {
                'con': p[1],
                'var': p[2],
                'block': p[3]  # 是一个表达式的list
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
            assign_statement = Assign()
            assign_statement.varRef = p[1]
            assign_statement.exp = p[3]
            assign_statement.line = p.lineno(1)
            assign_statement.type = "assign"
            assign_statement.stateType = "void"
            p[0] = assign_statement

            # 查错
            # 其余错误
            type = p[1].type
            type_e = Exp_type(p[3])
            # 数组引用错误
            if type[-1] == '1' or type_e[-1] == '1':
                self.error.append({
                    'type': '数组引用错误',
                    'line': p.lineno(2),
                    'value': p[1].varId + ' or ' + p[3].value
                })
                return
            # 表达式引用错误/变量引用错误
            if type == '' or type_e == 'error': return
            # 赋值是否合法 类型不同直接报错
            if p[3].type == 'var':
                if type != type_e:
                    self.error.append({
                        'type': '赋值不合法',
                        'line': p.lineno(2),
                        'value': "变量不匹配" + type + '!=' + p[3].varRef.type
                    })
            elif p[3].type == 'function':
                if type != type_e:
                    self.error.append({
                        'type': '赋值不合法',
                        'line': p.lineno(2),
                        'value': "函数" + p[3].value + "返回类型不匹配"
                    })
            elif p[3].type == 'compound':
                if type != type_e:
                    self.error.append({
                        'type': '赋值不合法',
                        'line': p.lineno(2),
                        'value': "表达式值不匹配：" + type + '!=' + p[3].value
                    })
            elif type != type_e:
                self.error.append({
                    'type': '赋值不合法',
                    'line': p.lineno(2),
                    'value': "值不匹配：" + type + '!=' + p[3].type
                })

        def p_statement_func_assign(p):
            'statement : func_id ASSIGNOP expression'
            # 在这里处理函数赋值语句的情况
            assign_statement = Assign()
            assign_statement.varRef = p[1]
            assign_statement.exp = p[3]
            assign_statement.line = p.lineno(1)
            assign_statement.type = "assign"
            assign_statement.stateType = "void"
            p[0] = assign_statement

            # 排错
            type = p[1].type
            type_e = Exp_type(p[3])

            if type == '' or type_e == 'error':
                return
            if p[3].type == 'var':
                if type != type_e:
                    self.error.append({
                        'type': '赋值不合法',
                        'line': p.lineno(2),
                        'value': "变量不匹配" + type + '!=' + p[3].varRef.type
                    })
            elif p[3].type == 'function':
                if type != type_e:
                    self.error.append({
                        'type': '赋值不合法',
                        'line': p.lineno(2),
                        'value': "函数" + p[3].value + "返回类型不匹配"
                    })
            elif p[3].type == 'compound':
                if type != type_e:
                    self.error.append({
                        'type': '赋值不合法',
                        'line': p.lineno(2),
                        'value': "表达式值不匹配：" + type + '!=' + p[3].value
                    })
            elif type != type_e:
                self.error.append({
                    'type': '赋值不合法',
                    'line': p.lineno(2),
                    'value': "值不匹配：" + type + '!=' + p[3].type
                })

        def p_func_id(p):
            'func_id : ID'
            var = VarReference(p[1], p.lineno(1), [])

            if p[1] == SymbolTable[-1]['id']:
                var.type = SymbolTable[-1]['type']
            elif SymbolTable[-1]['subF'].get(p[1]) != None:
                var.type = SymbolTable[-1]['subF'][p[1]][1]
            else:
                self.error.append({
                    'type': '函数名不存在',
                    'line': p.lineno(1),
                    'value': p[1]
                })
            p[0] = var

        def p_statement_procedure_call(p):
            'statement : procedure_call'
            # 在这里处理过程调用语句的情况
            p[0] = p[1]

        def p_statement_compound(p):
            'statement : compound_statement'
            # 在这里处理复合语句的情况
            compound_statement = Compound(p[1])
            compound_statement.line = p.lineno(1)
            compound_statement.type = "compound"
            compound_statement.stateType = "void"
            p[0] = [compound_statement]

        def p_statement_if(p):
            'statement : IF expression THEN statement else_part'
            # 在这里处理条件语句的情况
            if_statement = If()
            if_statement.condition = p[2]
            if_statement.then = p[4]
            if_statement.els = p[5]
            if_statement.line = p.lineno(1)
            if_statement.type = "if"
            if_statement.stateType = "void"
            p[0] = [if_statement]

        def p_statement_for(p):
            'statement : FOR ID ASSIGNOP expression TO expression DO statement'
            # 在这里处理for循环语句的情况
            for_statement = For()
            for_statement.id = p[2]
            for_statement.state = p[4]
            for_statement.end = p[6]
            for_statement.do = p[8]
            for_statement.line = p.lineno(1)
            for_statement.type = "for"
            for_statement.stateType = "void"
            p[0] = [for_statement]

        def p_statement_read(p):
            'statement : READ LPAREN variable_list RPAREN'
            # 在这里处理读取语句的情况
            read_statement = Scan()
            read_statement.varlist = p[3]
            read_statement.line = p.lineno(1)
            read_statement.type = "scan"
            read_statement.stateType = "void"
            p[0] = [read_statement]

        def p_statement_write(p):
            'statement : WRITE LPAREN expression_list RPAREN'
            # 在这里处理写入语句的情况
            write_statement = Print()
            write_statement.varlist = p[3]
            write_statement.line = p.lineno(1)
            write_statement.type = "print"
            write_statement.stateType = "void"
            p[0] = [write_statement]

        # 变量引用

        def p_variable_list_single(p):
            'variable_list : variable'
            # 在这里处理只有一个变量的情况
            p[0] = [p[1]]

        def p_variable_list_multiple(p):
            'variable_list : variable_list COM variable'
            # 在这里处理多个变量的情况
            p[0] = p[1] + [p[3]] if p[3] else p[1]

        def p_variable(p):
            'variable : ID id_varpart'
            var = VarReference(p[1], p.lineno(1), p[2]['exp'], p[2]['flag'])
            f = 0
            # 查变量、参数、常量
            for i in range(len(SymbolTable) - 1, -1, -1):
                for j, k in SymbolTable[i]['para'].items():
                    if p[1] in j:
                        var.type = str(k)
                        f = 1
                        break
                if f == 1:
                    break
                vp=SymbolTable[i]['var'].copy()
                vp = {**vp, **SymbolTable[i]['const']}
                if vp.get(p[1]) != None:
                    var.type = vp.get(p[1])
                    f = 1
                    break
            # 查函数名
            if f == 0:
                if p[1] == SymbolTable[-1]['id']:
                    var.type = SymbolTable[-1]['type']
                elif SymbolTable[-1]['subF'].get(p[1]) != None:
                    var.type = SymbolTable[-1]['subF'][p[1]][1]

            # 查错——exist
            if var.type in ['', None]:
                self.error.append({
                    'type': 'ID不存在',
                    'line': p.lineno(1),
                    'value': p[1]
                })
                p[2]['flag'] = 0
            # 数组下标标记 a[]
            # return ['type',lb,ub]
            if p[2]['flag'] == 1:
                if len(p[2]['exp']) != len(var.type[1]):
                    self.error.append({
                        'type': '数组下标错误',
                        'line': p.lineno(1),
                        'value': '数组应当为' + str(len(var.type[1])) + '维'
                    })
                else:
                    for i in range(0, len(p[2]['exp'])):
                        index = p[2]['exp'][i].value
                        if isinstance(p[2]['exp'][i].value,int):
                            if not var.type[1][i] <= index <= var.type[2][i]:
                                self.error.append({
                                    'type': '数组越界',
                                    'line': p.lineno(1),
                                    'value': p[1] + "的" + '维度' + str(i + 1) + ':range(' + str(
                                        var.type[1][i]) + ',' + str(var.type[2][i]) + ')'
                                })
                                break
                        else:
                            pass
                var.type = var.type[0][:-1]
            p[0] = var

        def p_id_varpart_empty(p):
            'id_varpart : empty'
            p[0] = {
                'exp': '',
                'flag': 0
            }
            # 在这里处理空的情况

        def p_id_varpart_with_indices(p):
            'id_varpart : LBRACKET expression_list RBRACKET'

            p[0] = {
                'exp': p[2],
                'flag': 1
            }

        def p_procedure_call_no_arg(p):
            'procedure_call : ID'
            # 在这里处理没有参数的过程调用情况
            procall_statement = ProcCall()
            procall_statement.procId = p[1]
            procall_statement.actParaList = []
            procall_statement.line = p.lineno(1)
            procall_statement.type = "procall"
            procall_statement.stateType = "void"
            p[0] = [procall_statement]
            # 排错
            if p[1] != SymbolTable[-1]['id'] and SymbolTable[-1]['subF'].get(p[1]) == None:
                self.error.append({
                    'type': '函数不存在',
                    'line': p.lineno(1),
                    'value': p[1]
                })
            elif SymbolTable[-1]['subF']!={} and SymbolTable[-1]['subF'].get(p[1])[1] != 'void':
                self.error.append({
                    'type': '这是函数而非过程',
                    'line': p.lineno(1),
                    'value': p[1]
                })


        def p_procedure_call_with_args(p):
            'procedure_call : ID LPAREN expression_list RPAREN'
            # 在这里处理带有参数的过程调用情况
            procall_statement = ProcCall()
            procall_statement.procId = p[1]
            procall_statement.actParaList = p[3]
            procall_statement.line = p.lineno(1)
            procall_statement.type = "procall"
            procall_statement.stateType = "void"
            p[0] = [procall_statement]
            # 排错
            print(p[1])
            if p[1] != SymbolTable[-1]['id'] and SymbolTable[-1]['subF'].get(p[1]) == None:
                self.error.append({
                    'type': '函数名不存在',
                    'line': p.lineno(1),
                    'value': p[1]
                })
            elif SymbolTable[-1]['subF']!={} and SymbolTable[-1]['subF'].get(p[1])[1] != 'void':
                self.error.append({
                    'type': '这是函数而非过程',
                    'line': p.lineno(1),
                    'value': p[1]
                })

        def p_procedure_call_no_args(p):
            'procedure_call : ID LPAREN RPAREN'
            # 在这里处理带有参数的过程调用情况
            procall_statement = ProcCall()
            procall_statement.procId = p[1]
            procall_statement.actParaList = {}
            procall_statement.line = p.lineno(1)
            procall_statement.type = "procall"
            procall_statement.stateType = "void"
            p[0] = [procall_statement]
            # 排错
            print(p[1])
            if p[1] != SymbolTable[-1]['id'] and SymbolTable[-1]['subF'].get(p[1]) == None:
                self.error.append({
                    'type': '函数名不存在',
                    'line': p.lineno(1),
                    'value': p[1]
                })
            elif SymbolTable[-1]['subF']!={} and SymbolTable[-1]['subF'].get(p[1])[1] != 'void':
                self.error.append({
                    'type': '这是函数而非过程',
                    'line': p.lineno(1),
                    'value': p[1]
                })


        def p_else_part(p):
            'else_part : ELSE statement'
            p[0] = p[2]

        def p_else_part_empty(p):
            'else_part : empty '
            p[0] = p[1]

        def p_expression_list_single(p):
            'expression_list : expression'
            # 在这里处理只有一个表达式的情况
            p[0] = [p[1]]

        def p_expression_list_multiple(p):
            'expression_list : expression_list COM expression'
            # 在这里处理多个表达式的情况
            p[0] = p[1] + [p[3]] if p[3] else p[1]

        def p_expression_simple(p):
            'expression : simple_expression'
            # 在这里处理单一简单表达式的情况
            ty = Exp_type(p[1])
            if (ty == 'error'):
                self.error.append({
                    'type': '表达式错误',
                    'line': p[1].line,
                    'value': p[1].subE1.type + "与" + p[1].subE2.type
                })
            if p[1].type == 'compound':
                p[1].value = ty
            p[0] = p[1]

        def p_expression_with_relational_op(p):
            '''expression : simple_expression relop simple_expression
                            '''
            # 在这里处理带有关系运算符的表达式情况
            fac = Expression('compound', p[1].line)
            fac.operation = p[2]
            fac.opType = 'double'
            fac.subE1 = p[1]
            fac.subE2 = p[3]

            # 检查双目运算符是否成立，将类型赋值给.value
            fac.value = Exp_type(fac)
            if (fac.value == 'error'):
                self.error.append({
                    'type': '表达式错误',
                    'line': p[1].line,
                    'value': p[1].type + " != " + p[3].type
                })
            p[0] = fac

        def p_relop(p):
            '''relop : RELOP
                    | EQUAL'''
            p[0] = p[1]

        def p_simple_expression_single_term(p):
            'simple_expression : term'
            # 在这里处理只有一个项的情况
            p[0] = p[1]

        def p_simple_expression_with_addop(p):
            'simple_expression : simple_expression ADDOP term'
            # 在这里处理带有加法运算符的表达式情况
            fac = Expression('compound', p.lineno(2))
            fac.operation = p[2]
            fac.opType = 'double'
            fac.subE1 = p[1]
            fac.subE2 = p[3]
            p[0] = fac

        def p_term_single_factor(p):
            'term : factor'
            # 处理只有一个因子的情况
            p[0] = p[1]

        def p_term_with_mulop(p):
            'term : term MULOP factor'
            # 处理带有乘法运算符的表达式情况
            fac = Expression('compound', p.lineno(2))
            fac.operation = p[2]
            fac.opType = 'double'
            fac.subE1 = p[1]
            fac.subE2 = p[3]
            p[0] = fac

        def p_factor_num(p):
            '''factor : NUM
                    | DIGITS'''
            # 处理数字的情况
            fac = Expression(str(type(p[1]))[8:-2], p.lineno(1), p[1])
            p[0] = fac

        def p_factor_variable(p):
            'factor : variable'
            # 处理变量的情况
            fac = Expression('var', p[1].line,p[1].varId)
            fac.varRef = p[1]
            if p[1].varId == SymbolTable[-1]['id'] or SymbolTable[-1]['subF'].get(p[1].varId) != None:
                fac = Expression('function', p[1].line, p[1].varId)
            
            p[0] = fac

        def p_factor_expression(p):
            'factor : LPAREN expression RPAREN'
            # 处理表达式的情况
            fac = Expression(p[2].type, p.lineno(1))
            fac.type='compound'
            fac.opType = 'damn'
            fac.subE1 = p[2]
            p[0] = fac

        def p_factor_function_call_no_argument(p):
            'factor : ID LPAREN RPAREN'
            fac=Expression('function',p.lineno(1),p[1])
            p[0]=fac

            if p[1] != SymbolTable[-1]['id'] and SymbolTable[-1]['subF'].get(p[1]) == None:
                self.error.append({
                    'type': '函数不存在',
                    'line': p.lineno(1),
                    'value': p[1]
                })
            else:
                # print("???")
                pass

        def p_factor_function_call(p):
            'factor : ID LPAREN expression_list RPAREN'
            # 处理函数调用的情况
            fac = Expression('function', p.lineno(1), p[1])
            fac.fucCall = FucCall(p[1], p.lineno(1), p[3])
            p[0] = fac
            # 排错
            if p[1] != SymbolTable[-1]['id'] and SymbolTable[-1]['subF'].get(p[1]) == None:
                self.error.append({
                    'type': '函数不存在',
                    'line': p.lineno(1),
                    'value': p[1]
                })
            else:
                # print("???")
                pass
            # expression_list
            # ID参数个数，类型

            # expression_list

        def p_factor_not(p):
            'factor : NOT factor'
            # 处理NOT运算符的情况
            fac = Expression('compound', p.lineno(1))
            fac.operation = p[1]
            fac.opType = 'damn'
            fac.subE1 = p[2]
            p[0] = fac

        def p_factor_addop(p):
            'factor : ADDOP factor'
            # 处理一元运算符的情况
            fac = Expression('compound', p.lineno(1))
            fac.operation = p[1]
            fac.opType = 'damn'
            fac.subE1 = p[2]
            p[0] = fac

        def p_factor_false(p):
            '''factor : FALSE'''
            # 处理false类型的情况
            fac = Expression('boolean', p.lineno(1), p[1])
            p[0] = fac

        def p_factor_true(p):
            '''factor : TRUE'''
            # 处理true类型的情况
            fac = Expression('boolean', p.lineno(1), p[1])
            p[0] = fac


        def p_error(p):
            if self.parse.token():
                raise yacc.YaccError("语法错误在第 %d 行，第 %d 列 %s" % (p.lineno, p.lexpos, p))
            else:
                raise yacc.YaccError("Syntax error at EOF")
        #调用lex，获取token，error，comment
        lexi = Lexer()
        lexi.build(name)
        tokens = lexi.token
        self.parse = yacc.yacc()
        return [lexi.error,lexi.COMMENT]

    def get_result(self, name):
        [lex_error,comment] = self.child(name)
        # 打开一个文件
        file = open(name, "r", encoding='utf-8')
        # 读取文件内容
        content = file.read().replace('\xa0', ' ')#.lower()
        result = self.parse.parse(content)

        return [result, lex_error,comment]


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
        # print(type(subprogram))
        print("Constant List:")
        for const_details in subprogram.constList["constant"] if subprogram.constList.get('constant') else {}:
            # print(f"  {const_id}:")
            print(f"    - Constant ID: {const_details.constId}")
            print(f"    - Line Number: {const_details.line}")
            print(f"    - Type: {const_details.type}")
            print(f"    - Value: {const_details.Value}\n")

        print("Variable List:")
        for var_details, var_id in subprogram.varList.items():
            print(f"  {var_id}:")
            print(f"    - ID List: {var_details.idlist}")
            print(f"    - type: ")
            self.print_Type(var_details.type)

        print("SubDefinition List:")
        print(subprogram.subDefList)
        print(f"   length:{subprogram.subDefList['length']}")
        print(f"   type:{subprogram.subDefList['type']}")
        for funcdef in subprogram.subDefList["subprograms"]:
            self.print_SubDef(funcdef)

        print("Block:")
        # print(subprogram.block.statements)
        self.print_statements(subprogram.block.statements)

    def print_Type(self, Type_ins):
        print(f"        type:{Type_ins.type}")
        print(f"        line:{Type_ins.line}")
        print(f"        arrFlag:{Type_ins.arrFlag}")
        if Type_ins.arrFlag:
            print(f"        dimention:{len(Type_ins.lB)}")
            print(f"        -lowerBound(lB):{Type_ins.lB}")
            print(f"        -upperBound(uB):{Type_ins.uB}")

    def print_SubDef(self, funcdef):
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
        for var_details, var_id in funcdef.varList.items():
            print(f"  {var_id}:")
            print(f"    - ID List: {var_details.idlist}")
            print(f"    - Type: {var_details.type.type}")
        print("Block of SubProgram:")
        self.print_statements(funcdef.block.statements)

    def print_formal_para(self, paralist):
        for para_detail, line_num in paralist.items():
            print(f"    line:{line_num}")
            print(f"    -paraId:{para_detail.paraId}")
            print(f"    -line:{para_detail.line}")
            print(f"    -type:{para_detail.type}")
            print(f"    -flag:{para_detail.flag}\n")

    def print_statements(self, statements):

        for statement in statements:
            if isinstance(statement, list) and statement:  # 确保 statement 是一个非空列表
                statement = statement[0]  # 访问列表的第一个元素
            if isinstance(statement, Assign):
                print("Assignment:")
                print(f"    line:{statement.line}")
                print(f"    State:{statement.stateType}")
                print(f"  Left-hand Side Variable: ")
                self.print_varReference(statement.varRef)
                print("  Right-hand Side Expression:")
                self.print_expression(statement.exp)

            elif isinstance(statement, If):
                print("If Statement:")
                print(f"    line:{statement.line}")
                print(f"    State:{statement.stateType}")
                print("  Condition:")
                self.print_expression(statement.condition)
                print("  Then Clause:")
                self.print_statements([statement.then])
                print("  Else Clause:")
                self.print_statements([statement.els])

            elif isinstance(statement, While):
                print("While Loop:")
                print(f"    line:{statement.line}")
                print(f"    State:{statement.stateType}")
                print("  Condition:")
                self.print_expression(statement.condition)
                print("  Do:")
                self.print_statements([statement.do])
            # Add other statement types as needed

            elif isinstance(statement, For):
                print("For Loop:")
                print(f"    line:{statement.line}")
                print(f"    State:{statement.stateType}")
                print(f"    Loop Variable: {statement.id}")
                print("    Start Value:")
                self.print_expression(statement.state)
                print("    End Value:")
                self.print_expression(statement.end)
                print("    Do:")
                self.print_statements([statement.do])

            elif isinstance(statement, Repeat):
                print("Repeat Statement:")
                print(f"    line:{statement.line}")
                print(f"    State:{statement.stateType}")
                print("    Condition:")
                self.print_expression(statement.condition)
                print("    Do:")
                self.print_statements([statement.do])

            elif isinstance(statement, Compound):
                print("Compound Statement:")
                print(f"    line:{statement.line}")
                print(f"    State:{statement.stateType}")
                print("    Block of Statements:")
                self.print_statements(statement.statements)

            elif isinstance(statement, ProcCall):
                print("Procedure Call:")
                print(f"    line:{statement.line}")
                print(f"    State:{statement.stateType}")
                print(f"    Procedure Name: {statement.procId}")
                print("    Actual Parameters:")
                for exp in statement.actParaList:
                    self.print_expression(exp)

            elif isinstance(statement, Print):
                print("Print Statement:")
                print(f"    line:{statement.line}")
                print(f"    State:{statement.stateType}")
                print("    Output Variables:")
                for one_var in statement.varlist:
                    self.print_expression(one_var)



            elif isinstance(statement, Scan):
                print("Scan Statement:")
                print(f"    line:{statement.line}")
                print(f"    State:{statement.stateType}")
                for var in statement.varlist:
                    self.print_varReference(var)

    def print_varReference(self, var):
        print("VarReference:")
        print(f"    varId:{var.varId}")
        print(f"    line:{var.line}")
        print(f"    flag:{var.flag}")
        if not isinstance(var.expList, str):
            for exp in var.expList:
                self.print_expression(exp)

    def print_expression(self, expression):
        if not expression:
            return
        print(f"Type: {expression.type}")
        print(f"line:{expression.line}")
        if expression.varRef is not None:
            self.print_varReference(expression.varRef)
        print(f"    value:{expression.value}")
        if expression.fucCall is not None:
            self.print_funcCall(expression.fucCall)
        print(f"    operation:{expression.operation}")
        print(f"    operationType:{expression.opType}")
        if expression.subE1 is not None:
            print("子表达式1：")
            self.print_expression(expression.subE1)
        if expression.subE2 is not None:
            print("子表达式2：")
            self.print_expression(expression.subE2)

    def print_funcCall(self, funcCall):
        print("函数调用：")
        print(f"    funcName:{funcCall.fucId}")
        print(f"    line:{funcCall.line}")
        for one_expression in funcCall.actParaList:
            if not isinstance(one_expression, str):
                self.print_expression(one_expression)


if __name__ == '__main__':

     pp=parser()
    #获取pascal程序名
     if len(sys.argv)==2:
         filename=sys.argv[1]
     elif len(sys.argv)==3 and sys.argv[1]=='-i':
         filename=sys.argv[2]
    #  filename=sys.argv[2] if len(sys.argv) > 1 and sys.argv[1]=='-i' else filename
    
     [result,lex_error,comment] = pp.get_result(filename)

    #  print(lex_error)
     #yacc_error为pp.error
     if pp.error != []:
        print(f"{'ERROR':^20}")
        print(f"{'type'!s:<15}{'line'!s:^6}{'value'!s:^10}")
        for item in pp.error:
            print('{name:<{len}}\t'.format(name=item['type'],len=15-len(item['type'].encode('GBK'))+len(item['type'])),end='')
            print(f"{item['line']:<6}{item['value']!s:<10}",end='\n')
         
    # #result["program"]就是一个Program实例
     printer = ProgramPrinter()
     printer.print_program_details(result["program"])
     
     Cfilename=filename.replace(".pas",".c")
     
    #  print("代码生成：")
     codeg=CodeGenerator()
     codeg.ast=result["program"]
     codeg.anaAst()
     codeg.genHeadFile()
     codeg.output(Cfilename)
     codeg.AddComment(comment,Cfilename)
     
    #comment是评论
     #输出注释，可通过成员变量COMMENT访问
    #  print(f"{'COMMENT':^20}") if comment!={} else print('无注释')
    #  for key,value in comment.items():
    #        print(f'line:{key[0]!s:<5} column:{key[1]!s:<5} value:{value!s:<10}')
