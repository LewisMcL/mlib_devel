import os
import re
from math import ceil, floor

class VerilogInstance(object):
    def __init__(self, entity='', name='', comment=None):
        """
        Construct an instance of entity 'entity'
        and instance name 'name'.
        Sourcefiles, if specified, is a list of sourcefiles (or directories)
        required to build this instance.
        You can add an optional comment string, which will appear in
        the resulting verilog file.
        """ 
        if len(entity) != 0:
            self.entity = entity
        else:
            raise ValueError("'entity' must be a string of non-zero length")
        if len(name) != 0:
            self.name = name
        else:
            raise ValueError("'entity' must be a string of non-zero length")
        self.ports = []
        self.parameters = []
        self.comment = comment
        self.wb_interfaces = 0
        self.wb_bytes = []
        self.wb_ids = []
        self.wb_names = []
        self.sourcefiles = []

    def add_sourcefile(self, file):
        self.sourcefiles.append(file)

    def add_port(self, name=None, signal=None):
        """
        Add a port to the instance, with name 'name', connected to signal
        'signal'. 'signal' can be a string, and might include bit indexing,
        e.g. 'my_signal[15:8]'
        """
        self.ports.append({'name':name, 'signal':signal})
    
    def add_wb_interface(self,nbytes=4,name=None):
        """
        Add the ports necessary for a wishbone slave interface.
        Wishbone ports that depend on the slave index are identified by a parameter
        that matches the instance name. This parameter must be given a value in a higher level
        of the verilog code!
        """
        self.wb_interfaces += 1
        self.wb_bytes += [nbytes]
        if name is None:
            wb_id = self.name.upper() + '_WBID%d'%(self.wb_interfaces-1)
            self.wb_names += [self.name]
        else:
            wb_id = name.upper() + '_WBID%d'%(self.wb_interfaces-1)
            self.wb_names += [name]
        self.wb_ids += [wb_id]
        self.add_port('wb_clk_i','wb_clk_i')
        self.add_port('wb_rst_i','wb_rst_i')
        self.add_port('wb_cyc_i','wbs_cyc_o[%s]'%wb_id)
        self.add_port('wb_stb_i','wbs_stb_o[%s]'%wb_id)
        self.add_port('wb_we_i','wbs_we_o')
        self.add_port('wb_sel_i','wbs_sel_o')
        self.add_port('wb_adr_i','wbs_adr_o')
        self.add_port('wb_dat_i','wbs_dat_o')
        self.add_port('wb_dat_o','wbs_dat_i[(%s+1)*32-1:(%s)*32]'%(wb_id,wb_id))
        self.add_port('wb_ack_o','wbs_ack_i[%s]'%wb_id)
        self.add_port('wb_err_o','wbs_err_i[%s]'%wb_id)

    def add_parameter(self, name=None, value=None):
        """
        Add a parameter to the instance, with name 'name' and value
        'value'
        """
        self.parameters.append({'name':name, 'value':value})
    
    def gen_instance_verilog(self):
        s = ''
        if self.comment is not None:
            s += '  // %s\n'%self.comment
        s += '  %s #(\n' %self.entity
        n_params = len(self.parameters)
        for pn,parameter in enumerate(self.parameters):
            s += '    .%s(%s)'%(parameter['name'],parameter['value'])
            if pn != (n_params - 1):
                s += ',\n'
            else:
                s += '\n'
        s += '  ) %s (\n'%self.name
        n_ports = len(self.ports)
        for pn,port in enumerate(self.ports):
            s += '    .%s(%s)'%(port['name'],port['signal'])
            if pn != (n_ports - 1):
                s += ',\n'
            else:
                s += '\n'
        s += '  );\n'
        return s

class VerilogModule(object):
    def __init__(self, name='', topfile=None):
        """
        Construct a new module, named 'name'
        """
        if len(name) != 0:
            self.name = name
        else:
            raise ValueError("'name' must be a string of non-zero length")
        
        self.topfile = topfile
        self.ports = []
        self.parameters = []
        self.localparams = []
        self.signals = []
        self.instances = []
        self.assignments = []
        self.raw_str = ''
        self.wb_slaves = 0
        self.wb_base = []
        self.wb_high = []
        self.wb_name = []
        self.get_base_wb_slaves()
        self.sourcefiles = []

    def wb_compute(self, base_addr=0x10000, alignment=4):
        # base_addr: the lowest address allowed for user IP is reserved+1
        # alignment: start addresses must be a multiple of alignment
        for inst in self.instances:
            for n in range(inst.wb_interfaces):
                print "Found new WB slave!"
                self.wb_base += [base_addr]
                self.wb_high += [base_addr + (alignment*int(ceil(inst.wb_bytes[n]/float(alignment)))) - 1]
                self.wb_name += [inst.wb_names[n]]
                self.add_localparam(name=inst.wb_ids[n], value=self.wb_slaves+self.base_wb_slaves)
                base_addr = self.wb_high[-1] + 1
                self.wb_slaves += 1

    def get_base_wb_slaves(self):
        fh = open('%s'%self.topfile, 'r')
        while(True):
            line = fh.readline()
            if len(line) == 0:
                break
            elif line.lstrip(' ').startswith('localparam N_WB_SLAVES'):
                print 'Found N_WB_SLAVES declaration'
                declaration = line.split('//')[0]
                self.base_wb_slaves = int(re.search('\d+',declaration).group(0))
                fh.close()
                break

    def add_port(self, name, dir, width=None, comment=None, **kwargs):
        """
        Add a port to the module, with a given name, width and dir.
        Any width other than None implies a vector port. I.e., width=1
        will generate port declarations of the form '*put [0:0] some_port;'
        Direction should be 'in', 'out' or 'inout'.
        You can optionally specify a comment to add to the port. 
        """
        self.ports.append({'name':name, 'width':width, 'dir':dir,
                           'comment':comment, 'attr':kwargs})

    def add_parameter(self, name, value, comment=None):
        """
        Add a parameter to the entity, with name 'parameter' and value
        'value'.
        You may add a comment that will end up in the generated verilog.
        """
        self.parameters.append({'name':name, 'value':value, 'comment':comment})


    def add_localparam(self, name, value, comment=None):
        """
        Add a parameter to the entity, with name 'parameter' and value
        'value'.
        You may add a comment that will end up in the generated verilog.
        """
        self.localparams.append({'name':name, 'value':value, 'comment':comment})

    def add_signal(self, signal, width=None, comment=None):
        """
        Add an internal signal to the entity, with name 'signal'
        and width 'width'.
        You may add a comment that will end up in the generated verilog.
        """
        self.signals.append({'name':signal, 'width':width, 'comment': comment})

    def assign_signal(self, lhs, rhs, comment=None):
        """
        Assign one signal to another, or one signal to a port.
        i.e., generate lines of verilog like:
        assign lhs = rhs;
        'lhs' and 'rhs' are strings that can represent port or signal
        names, and may include verilog-style indexing, eg '[15:8]'
        You may add a comment that will end up in the generated verilog.
        """
        self.assignments.append({'lhs':lhs, 'rhs':rhs, 'comment':comment})

    def add_new_instance(self, entity, name, comment=None):
        """
        Instantiate and return a new instance of entity 'entity', with instance name 'name'.
        You may add a comment that will end up in the generated verilog.
        """
        new_inst = VerilogInstance(entity=entity, name=name, comment=comment)
        self.instances.append(new_inst)
        return new_inst

    def add_sourcefile(self,file):
        self.sourcefiles.append(file)

    def add_instance(self, inst):
        """
        Add an existing instance to the list of instances in the module.
        """
        if isinstance(inst,VerilogInstance):
            self.instances.append(inst)
            self.sourcefiles += inst.sourcefiles
        else:
            raise ValueError('inst is not a VerilogInstance instance!')

    def add_raw_string(self,s):
        self.raw_str += s

    def gen_module_file(self):
        if self.topfile is None:
            self.write_new_module_file()
        else:
            self.rewrite_module_file()

    #def wb_compute(self):
    #    '''
    #    Count the number of wishbone slaves in the system, and set their
    #    base and high addresses
    #    '''
    #    base_addr = 0
    #    for inst in self.instances:
    #        if inst.wb_interfaces > 0:
    #            for n in range(inst.wb_interfaces):
    #                self.wb_base.append(base_addr)
    #                self.wb_high.append(base_addr + inst.wb_bytes[n] - 1)
    #                base_addr += inst.wb_bytes[n]
    #                wb_name = 'wb_'+ inst.name + '%s'%n
    #                self.wb_name.append(wb_name)
    #                self.add_parameter(name=wb_name, value=self.wb_interfaces)
    #                self.wb_interfaces += 1

    def rewrite_module_file(self):
        os.system('mv %s %s.base'%(self.topfile,self.topfile))
        fh_base = open('%s.base'%self.topfile,'r')
        fh_new = open('%s'%self.topfile, 'w')
        fh_new.write('// %s, AUTOMATICALLY MODIFIED BY PYTHON\n\n'%self.topfile)
        while(True):
            line = fh_base.readline()
            if len(line) == 0:
                break
            elif line.lstrip(' ').startswith('module'):
                print 'Found module declaration'
                fh_new.write(line)
                fh_new.write(self.gen_port_list())
            elif line.lstrip(' ').startswith('localparam N_WB_SLAVES'):
                print 'Found N_WB_SLAVES declaration'
                declaration = line.split('//')[0]
                base_package_slaves = int(re.search('\d+',declaration).group(0))
                print 'base_packages slaves?',base_package_slaves
                s = re.sub('\d+','%s'%(self.wb_slaves+base_package_slaves),declaration)
                print s
                fh_new.write(s)
            elif line.lstrip(' ').startswith('localparam SLAVE_BASE = {'):
                print 'Found slave_base dec'
                fh_new.write(line)
                for slave in range(self.wb_slaves)[::-1]:
                    fh_new.write("    32'h%08x, // %s\n"%(self.wb_base[slave], self.wb_name[slave]))
            elif line.lstrip(' ').startswith('localparam SLAVE_HIGH = {'):
                print 'Found slave_high dec'
                fh_new.write(line)
                for slave in range(self.wb_slaves)[::-1]:
                    fh_new.write("    32'h%08x, // %s\n"%(self.wb_high[slave], self.wb_name[slave]))
            elif line.lstrip(' ').startswith('endmodule'):
                fh_new.write(self.gen_top_mod())
                fh_new.write(line)
            else:
                fh_new.write(line)
        fh_new.close()
        fh_base.close()

    def write_new_module_file(self):
        mod_dec        = self.gen_mod_dec_str()
        # declare inputs/outputs with the module dec
        #port_dec       = self.gen_ports_dec_str()
        param_dec      = self.gen_params_dec_str()
        localparam_dec = self.gen_localparams_dec_str()
        sig_dec        = self.gen_signals_dec_str()
        inst_dec       = self.gen_instances_dec_str()
        assignments    = self.gen_assignments_str()
        endmod         = self.gen_endmod_str()
        fh = open('%s.v'%self.name, 'w')
        fh.write('// MODULE %s, AUTOMATICALLY GENERATED BY PYTHON\n\n'%self.name)
        fh.write('\n')
        fh.write('\n')
        fh.write(mod_dec)
        fh.write('\n')
        fh.write(port_dec)
        fh.write('\n')
        fh.write(param_dec)
        fh.write('\n')
        fh.write(localparam_dec)
        fh.write('\n')
        fh.write(sig_dec)
        fh.write('\n')
        fh.write(inst_dec)
        fh.write('\n')
        fh.write(assignments)
        fh.write('\n')
        fh.write(self.raw_str)
        fh.write('\n')
        fh.write(endmod)
        fh.close()

    def gen_top_mod(self):
        """
        Generate the code that needs to go in a top level verilog file
        to incorporate this module
        """        
        # don't need this if we declare ports with the module declaration
        port_dec         = ''#self.gen_ports_dec_str()
        param_dec        = self.gen_params_dec_str()
        localparam_dec   = self.gen_localparams_dec_str()
        sig_dec          = self.gen_signals_dec_str()
        inst_dec         = self.gen_instances_dec_str()
        assignments      = self.gen_assignments_str()
        s = '// INSTANCE %s, AUTOMATICALLY GENERATED BY PYTHON\n'%self.name
        s += '\n'
        s += port_dec
        s += '\n'
        s += param_dec
        s += '\n'
        s += localparam_dec
        s += '\n'
        s += sig_dec
        s += '\n'
        s += inst_dec
        s += '\n'
        s += assignments
        s += '\n'
        s += self.raw_str
        return s
        
    def gen_mod_dec_str(self):
        """
        Generate the verilog code required to start a module
        declaration.
        """
        s = 'module %s (\n'%self.name
        n_ports = len(self.ports)
        for pn,port in enumerate(self.ports):
            if port['width'] is None:
                s += '    %s %s'%(kwm[port['dir']],port['name'])
            else:
                s += '    %s [%d:0] %s'%(kwm[port['dir']], (port['width']-1), port['name'])
            if pn != (n_ports-1):
                s += ','
            if port['comment'] is not None:
                s += ' // %s'%port['comment']
            s += '\n'
        s += '  );\n'
        return s

    def gen_params_dec_str(self):
        """
        Generate the verilog code required to
        declare ports
        """
        s = ''
        for pn,parameter in enumerate(self.parameters):
            s += '  parameter %s = %s;'%(parameter['name'],parameter['value'])
            if parameter['comment'] is not None:
                s += ' // %s'%parameter['comment']
            s += '\n'
        return s

    def gen_localparams_dec_str(self):
        """
        Generate the verilog code required to
        declare ports
        """
        s = ''
        for pn,parameter in enumerate(self.localparams):
            s += '  localparam %s = %s;'%(parameter['name'],parameter['value'])
            if parameter['comment'] is not None:
                s += ' // %s'%parameter['comment']
            s += '\n'
        return s

    def gen_port_list(self):
        s = ''
        kwm = {'in':'input','out':'output','inout':'inout'}
        for pn,port in enumerate(self.ports):
            if port['width'] is None:
                s += '    %s %s,'%(kwm[port['dir']],port['name'])
            else:
                s += '    %s [%d:0] %s,'%(kwm[port['dir']], (port['width']-1), port['name'])
            if port['comment'] is not None:
                s += ' // %s'%port['comment']
            s += '\n'
        return s

    def gen_ports_dec_str(self):
        """
        Generate the verilog code required to
        declare parameters
        """
        # keyword map
        kwm = {'in':'input','out':'output','inout':'inout'}
        s = ''
        for pn,port in enumerate(self.ports):
            # set up indentation nicely
            s += '  '
            # first write attributes
            if port['attr'] != {}:
                s += '(* '
                n_keys = len(port['attr'].keys())
                for kn,key in enumerate(port['attr'].keys()):
                    if kn != (n_keys-1):
                        s += '%s = "%s",'%(key,port['attr'][key])
                    else:
                        s += '%s = "%s"'%(key,port['attr'][key])
                s += ' *)'
            # declare port
            if port['width'] is None:
                s += '%s %s;'%(kwm[port['dir']], port['name'])
            else:
                s += '%s [%d:0] %s;'%(kwm[port['dir']], (port['width']-1), port['name'])
            if port['comment'] is not None:
                s += ' // %s'%port['comment']
            s += '\n'
        return s
       
    def gen_signals_dec_str(self):
        """
        Generate the verilog code required to
        declare signals
        """
        s = ''
        for sn,sig in enumerate(self.signals):
            if sig['width'] is None:
                s += '  wire %s;'%(sig['name'])
            else:
                s += '  wire [%d:0] %s;'%((sig['width']-1), sig['name'])
            if sig['comment'] is not None:
                s += ' // %s'%sig['comment']
            s += '\n'
        return s

    def gen_instances_dec_str(self):
        """
        Generate the verilog code required
        to instantiate the instances in this 
        module
        """
        n_inst = len(self.instances)
        s = ''
        for n,instance in enumerate(self.instances):
            s += instance.gen_instance_verilog()
            if n != (n_inst - 1):
                s += '\n'
        return s
    
    def gen_assignments_str(self):
        """
        Generate the verilog code required
        to assign a port or signal to another
        signal
        """
        s = ''
        for n,assignment in enumerate(self.assignments):
            s += '  assign %s = %s;'%(assignment['lhs'], assignment['rhs'])
            if assignment['comment'] is not None:
                s += ' // %s'%assignment['comment']
            s += '\n'
        return s

    def gen_endmod_str(self):
        return 'endmodule\n'
