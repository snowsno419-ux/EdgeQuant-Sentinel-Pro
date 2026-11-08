import ast, pathlib, unittest
class BEScopeTests(unittest.TestCase):
    def test_scope_restricts_layer_and_unknown(self):
        tree=ast.parse((pathlib.Path(__file__).parent/'edgequant_auto.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='auto_be_ticket_allowed')
        ns={'AUTO_BE_LAYER_SCOPE':'SIGNAL','AUTO_BE_LAYER_TICKETS':{('A',11):1,('A',12):2}, 'AUTO_BE_ENABLED':True}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'<scope>','exec'),ns)
        check=ns['auto_be_ticket_allowed']
        self.assertFalse(check(11,'A'));self.assertTrue(check(12,'A'))
        self.assertFalse(check(12,'B'));self.assertFalse(check(13,'A'))
        ns['AUTO_BE_LAYER_SCOPE']='ALL';self.assertTrue(check(11,'A'))
        ns['AUTO_BE_LAYER_SCOPE']='QUICK';self.assertTrue(check(11,'A'));self.assertFalse(check(12,'A'))
        ns['AUTO_BE_ENABLED']=False;self.assertFalse(check(11,'A'))
if __name__=='__main__':unittest.main()
