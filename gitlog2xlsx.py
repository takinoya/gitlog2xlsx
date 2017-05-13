#!/usr/bin/python3
""" Generate XLSX file which contains pick upped git log information

Copyright (C) 2017 Sakae.OTAKI<niagara.ta.ki.no@gmail.com>

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

   1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.

   2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.

   3. This notice may not be removed or altered from any source
   distribution.

<<ToDo>> write description.
"""

import os
import sys
import re
import subprocess
import argparse

import configparser

import xlsxwriter

class G2XSheetElement :
	"""
	Class for entries on the XLSX Report-Sheet
	"""
	def __init__(self) :
		self.commit_ID = None
		self.commit_date = None
		self.commit_subject = None
		self.commit_body = None
		self.hit_dict = {}
		
class G2XSheet :
	"""
	Class for a XLSX Report-Sheet
	"""
	def __init__(self) :
		self.sheet_name = None
		self.key_lst = []
		self.src_lst = []
		self.usr_lst = []
		self.elements = []

class G2XReporter :
	"""
	Class for a gitlog2xlsx Report management
	"""
	
	def _debug_mesg(self, mesg) :
		"""
		Output debug message to stderr if debug enabled.
		"""
		if self.debug :
			print('<<Debug>>:', mesg, file=sys.stderr)
			
	def _warn_mesg(self, mesg) :
		"""
		Output warning message to stderr
		"""
		print('<<Warning>>:', mesg, file=sys.stderr)
		
	def  __init__(self, vars_dict) :
		self.configured = False
		
		### Initialize from vars_dict ###
		self.debug           = vars_dict.get('debug', False)
		self.config          = vars_dict.get('config', None)
		self._debug_mesg(".config = " + self.config.__str__() )
		self.gitrange        = vars_dict.get('range', None)
		self._debug_mesg(".gitrange = " + self.gitrange.__str__() )
		self.since           = vars_dict.get('since', None)
		self._debug_mesg(".since = " + self.since.__str__() )
		self.until           = vars_dict.get('until', None)
		self._debug_mesg(".until = " + self.until.__str__() )
		self.xlsx            = vars_dict.get('xlsx', None)
		self._debug_mesg(".xlsx = " + self.xlsx.__str__() )
		self.prjroot         = vars_dict.get('prjroot', None)
		self._debug_mesg(".prjroot = " + self.prjroot.__str__() )
		self.git_mirror_path = vars_dict.get('git', None)
		self._debug_mesg(".git_mirror_path = " + self.git_mirror_path.__str__() )
		
		self.org_work_dir = os.path.abspath(os.getcwd() )
		if self.prjroot is None :
			self.prjroot = self.org_work_dir
			self._debug_mesg("No 'prjroot' option found. Assumed current dir is prjroot.")
			
		self.xlsx_enabled = False
		if self.xlsx is not None :
			self.xlsx_abspath = os.path.abspath(self.xlsx)
			self.xlsx_dir = os.path.dirname(self.xlsx_abspath)
			if os.path.exists(self.xlsx_dir) :
				self._debug_mesg("xlsx: [Enabled] " + self.xlsx_abspath)
				self.xlsx_enabled = True
			else :
				self._warn_mesg("xlsx: [Disabled] Directory " + self.xlsx_dir + " is not exist. Continue without xlsx.")
				
		self.nr_commit = 0
		self.commit_ID_lst = []
		self.check_date = subprocess.getoutput("date --iso-8601=seconds")
		self.host_info = subprocess.getoutput("uname -a")
		self.sheet_lst = []
		self.summary_elements = []
		
		if self.gitrange is not None :
			self.git_log_range_opt = " " + self.gitrange.__str__()
		else :
			self.git_log_range_opt = ""
		
		if self.since is not None :
			self.git_log_sdate_opt = " --since='" + self.since.__str__() + "'"
		else :
			#self.git_log_sdate_opt = " --since='1 weeks ago'"
			self.git_log_sdate_opt = ""
			
		if self.until is not None :
			elf.git_log_sdate_opt += " --until='" + self.until.__str__() + "'"
		
	def _load_config(self) :
		"""
		loading sheet parameters from configuration file
		"""
		if self.config is None :
			self._debug_mesg("self.config is not specified. Use default.")
			self.config = self.org_work_dir + '/gitlog2xlsx.conf'
		
		self._debug_mesg('load_config: ' + self.config.__str__() )
		
		ini = configparser.SafeConfigParser()
		ini.read(self.config)
		
		### global config ###
		if self.git_mirror_path is None :
			if ini.has_option('configuration', 'git_mirror_path') :
				self.git_mirror_path = ini.get('configuration', 'git_mirror_path')
			else :
				debug_mesg("git_mirror_path is not specified. Use default.")
				self.git_mirror_path = self.prjroot + "/linux.git"
				
		if ini.has_option('configuration', 'xlsx_commit_link_format') :
			self.xlsx_commit_link_enable = True
			self.xlsx_commit_link_format = ini.get('configuration', 'xlsx_commit_link_format')
		else :
			self.xlsx_commit_link_enable = False
		
		if self.xlsx_commit_link_enable :
			self._debug_mesg('[Enabled] .xlsx_commit_link_format : ' + self.xlsx_commit_link_format)
		else :
			self._debug_mesg('[Disabled] .xlsx_commit_link_format')
			
		### per sheet section ###
		self.sheet_lst = []
		sections = ini.sections()
		for wsheet in sections :
			wsheet_name = re.findall('(?<=^worksheet::).+$', wsheet)
			if wsheet_name :
				self._debug_mesg('detect worksheet setting: ' + wsheet_name[0])
				idx = len(self.sheet_lst)
				self.sheet_lst.append(G2XSheet() )
				self.sheet_lst[idx].sheet_name = wsheet_name[0]
				key_lst = ini.get(wsheet, 'keywords').lstrip().split('\n')
				self.sheet_lst[idx].key_lst = list(filter(lambda s:s != '', key_lst) )	# remove void member using lambda
				src_lst = ini.get(wsheet, 'src_list').lstrip().split('\n')
				self.sheet_lst[idx].src_lst = list(filter(lambda s:s != '', src_lst) )	# remove void member using lambda
				usr_lst = ini.get(wsheet, 'usr_list').lstrip().split('\n')
				self.sheet_lst[idx].usr_lst = list(filter(lambda s:s != '', usr_lst) )	# remove void member using lambda
				
				self._debug_mesg("+-- " + self.sheet_lst[idx].key_lst.__str__() )
				self._debug_mesg("+-- " + self.sheet_lst[idx].src_lst.__str__() )
				
		self.configured = True
		
	def _mark_to_sheet_data(self):
		### Entering git repository ###
		os.chdir(self.git_mirror_path)
		self._debug_mesg("Entering:" + os.getcwd() )
		
		### update commit ID list in required duration ###
		self._debug_mesg("CMD: " + "git log --format='%H' "  + self.git_log_sdate_opt + self.git_log_range_opt)
		raw_commit_ID_lst = subprocess.getoutput("git log --format='%H' "  + self.git_log_sdate_opt + self.git_log_range_opt)
		#self._debug_mesg("raw_commit_ID_lst: " + raw_commit_ID_lst.__str__() )
		self.commit_ID_lst    = raw_commit_ID_lst.split('\n')
		#self._debug_mesg("commit_ID_lst: " + self.commit_ID_lst.__str__() )
		
		nr_commit_ID = len(self.commit_ID_lst)
		nr_progress = 0

		### Analyze per commits ###
		for commitID in self.commit_ID_lst :
			nr_progress += 1
			if ( (nr_progress % 100) == 0 ) :
				print("[" + nr_progress.__str__() + "/" + nr_commit_ID.__str__() + "]", file=sys.stderr)
			
			self._debug_mesg(commitID.__str__() + " is seached.")
			### Get subject ###
			subject  = subprocess.getoutput("git log --format='%s' " + commitID + "^!")
			### Get commit date ###
			ci_date  = subprocess.getoutput("git log --format='%ci' " + commitID + "^!")
			### Get body of commit message (for searching) ###
			try :
				msg = subprocess.getoutput("git log --format='%s%n%n%b' " + commitID + "^!")
			except UnicodeDecodeError as err :
				msg = "<<Error: {0} >>".format(err)
			except :
				msg = "<<Error: Unexpected exception occurred>>"
			### Get medium formatted commit message (for output) ###
			try :
				msg_medium = subprocess.getoutput("git log --numstat --format=medium " + commitID + "^! | expand -t4")
			except UnicodeDecodeError as err :
				msg_medium = "<<Error: {0} >>".format(err)
			except :
				msg_medium = "<<Error: Unexpected exception occurred>>"
			### Get numstat ###
			#numstats = subprocess.getoutput("git log --numstat --format='' " + commitID + "^! | cut -f3").split()
			numstats = subprocess.getoutput("git log --numstat --format='' " + commitID + "^! | cut -f3")
			
			summary_idx = len(self.summary_elements)
			self.summary_elements.append(G2XSheetElement() )
			self.summary_elements[summary_idx].commit_ID = commitID
			self.summary_elements[summary_idx].commit_date = ci_date
			self.summary_elements[summary_idx].commit_subject = subject
			self.summary_elements[summary_idx].commit_body = msg_medium
			
			for ws in self.sheet_lst :
				hit_in_ws = False
				### Prepare storage ###
				idx = len(ws.elements)
				ws.elements.append(G2XSheetElement() )
				ws.elements[idx].commit_ID = commitID
				ws.elements[idx].commit_date = ci_date
				ws.elements[idx].commit_subject = subject
				ws.elements[idx].commit_body = msg_medium
				
				### update keyword hit dictionary ###
				if ws.key_lst :
					for kw in ws.key_lst :
						if re.search(kw, msg, re.IGNORECASE) :
							ws.elements[idx].hit_dict["keyword::" + kw] = True
							hit_in_ws = True
							self._debug_mesg("+-- [Hit] " + ws.sheet_name + " : keyword::" + kw)
						else :
							ws.elements[idx].hit_dict["keyword::" + kw] = False
				### update src_lst hit dictionary ###
				if ws.src_lst :
					for s in ws.src_lst :
						if re.search(s, numstats) :
							ws.elements[idx].hit_dict["src::" + s] = True
							hit_in_ws = True
							self._debug_mesg("+-- [Hit] " + ws.sheet_name + " : src::" + s)
						else :
							ws.elements[idx].hit_dict["src::" + s] = False
							
				### update hit by sheet name dictionary ###
				self.summary_elements[summary_idx].hit_dict[ws.sheet_name] = hit_in_ws
				
			### Debug ###
			self._debug_mesg(self.summary_elements[summary_idx].hit_dict.__str__() )
		
		### Leave git repository ###
		os.chdir(self.org_work_dir)
	
	def _write_a_environment_sheet(self) :
		### For console ###
		print('Environment')
		print('-----------')
		print('prjroot = ', self.prjroot)
		print('config = ', self.config)
		print('path of git_mirrorr = ', self.git_mirror_path)
		print('host info = ', self.host_info)
		print('operation date = ', self.check_date)
		print('git revision range string =', self.git_log_range_opt)
		print('git date duration string =', self.git_log_sdate_opt)
		print('')
		
		### For xlsx ###
		if self.xlsx_enabled :
			ws = self._workbook.add_worksheet('_Environment_')
			row_idx_base = 1
			col_idx_base = 1
			ws.write(row_idx_base + 0, col_idx_base + 0, 'prjroot = ' + self.prjroot.__str__() )
			ws.write(row_idx_base + 1, col_idx_base + 0, 'config = ' + self.config.__str__() )
			ws.write(row_idx_base + 2, col_idx_base + 0, 'path of git_mirrorr = ' + self.git_mirror_path.__str__() )
			ws.write(row_idx_base + 3, col_idx_base + 0, 'host info = ' + self.host_info.__str__() )
			ws.write(row_idx_base + 4, col_idx_base + 0, 'operation date = ' + self.check_date.__str__() )
			ws.write(row_idx_base + 5, col_idx_base + 0, 'git revision range string = ' + self.git_log_range_opt.__str__() )
			ws.write(row_idx_base + 6, col_idx_base + 0, 'git date duration string = ' + self.git_log_sdate_opt.__str__() )
			
	def _write_a_summary_sheet(self) :
		### For console ###
		print('Commit summary')
		print('--------------')
		if len(self.summary_elements) :
			for e in self.summary_elements :
				print('+--', e.commit_ID, e.commit_date)
				print('\t+--', e.commit_subject)
				for key,value in e.hit_dict.items() :
					if value :
						print('\t\t+-- [Hit]', key)
		print('')
		
		### For xlsx ###
		if self.xlsx_enabled :
			ws = self._workbook.add_worksheet('_Summary_')
			row_idx_base = 1
			col_idx_base = 1
			
			##### worksheet summary header #####
			row_idx = row_idx_base + 0
			ws.write_string(row_idx, col_idx_base + 0, 'Commit hash ID')
			ws.write_string(row_idx, col_idx_base + 1, 'Date')
			ws.write_string(row_idx, col_idx_base + 2, 'Subject')
			ws.set_column(col_idx_base + 0, col_idx_base + 1, 25)
			ws.set_column(col_idx_base + 2, col_idx_base + 2, 80)
			ws.set_row(row_idx, 200, None)
			if len(self.summary_elements) :
				col_idx = col_idx_base + 3
				for key,value in self.summary_elements[0].hit_dict.items() :
					ws.write_string(row_idx, col_idx, key, self._xlsx_cellform_rotate_m90)
					ws.set_column(col_idx, col_idx, 2.0)
					col_idx += 1
				ws.autofilter(1, col_idx_base + 3, 1, col_idx - 1)
			
			##### worksheet summary body #####
			row_idx += 1
			if len(self.summary_elements) :
				for e in self.summary_elements :
					commit_link = self.xlsx_commit_link_format.format(commitID=e.commit_ID)
					ws.write_url(row_idx, col_idx_base + 0, commit_link, self._xlsx_cellform_link, e.commit_ID)
					ws.write_string(row_idx, col_idx_base + 1, e.commit_date)
					ws.write_url(row_idx, col_idx_base + 2, commit_link, self._xlsx_cellform_link, e.commit_subject)
					col_idx = col_idx_base + 3
					for key,value in e.hit_dict.items() :
						if value :
							ws.write_string(row_idx, col_idx, 'X')
						col_idx += 1
					row_idx +=1

	def _write_a_result_sheet(self, sheetInfo) :
		### For console ###
		print('worksheet::' + sheetInfo.sheet_name)
		print("-" * (len('worksheet::' + sheetInfo.sheet_name) ) )
		for e in sheetInfo.elements :
			first_hit = True
			for key,value in e.hit_dict.items() :
				if value :
					if first_hit :
						print('+--', e.commit_ID, e.commit_date)
						print('\t+--', e.commit_subject)
						first_hit = False
					print('\t\t+-- [Hit]', key)
		print('')
		
		### For xlsx ###
		if self.xlsx_enabled :
			##### Create a new worksheet #####
			ws = self._workbook.add_worksheet(sheetInfo.sheet_name)
			
			##### worksheet header #####
			row_idx_base = 1
			col_idx_base = 1
			ws.write_string(row_idx_base, col_idx_base + 0, 'Commit hash ID')
			ws.write_string(row_idx_base, col_idx_base + 1, 'Date')
			ws.write_string(row_idx_base, col_idx_base + 2, 'Subject')
			ws.write_string(row_idx_base, col_idx_base + 3, 'Message (medium + numstat)')
			ws.set_column(col_idx_base + 0, col_idx_base + 1, 15)
			ws.set_column(col_idx_base + 2, col_idx_base + 2, 56)
			ws.set_column(col_idx_base + 3, col_idx_base + 3, 64)
			ws.set_row(row_idx_base, 200, None)
			if len(sheetInfo.elements) :
				col_idx = col_idx_base + 4
				for key,value in sorted(sheetInfo.elements[0].hit_dict.items() ) :
					ws.write_string(row_idx_base, col_idx, key, self._xlsx_cellform_rotate_m90)
					ws.set_column(col_idx, col_idx, 2.0)
					col_idx += 1
				usr_col_idx_head = col_idx
				for key in sheetInfo.usr_lst :
					ws.write_string(row_idx_base, col_idx, key, self._xlsx_cellform_rotate_m90)
					ws.set_column(col_idx, col_idx, 2.0)
					col_idx += 1
				merge_form = self._workbook.add_format({'align': 'center'})
				ws.merge_range(0, 1, 0, usr_col_idx_head - 1, "Auto generated information", merge_form)
				ws.autofilter(1, col_idx_base + 4, 1, col_idx - 1)
			row_idx = row_idx_base + 1
			##### worksheet body #####
			for e in sheetInfo.elements :
				first_hit = True
				col_idx = col_idx_base + 4
				for key,value in sorted(e.hit_dict.items() ) :
					if value :
						if first_hit :
							commit_link = self.xlsx_commit_link_format.format(commitID=e.commit_ID)
							ws.write_url(row_idx, col_idx_base + 0, commit_link, self._xlsx_cellform_link, e.commit_ID)
							ws.write_string(row_idx, col_idx_base + 1, e.commit_date)
							ws.write_url(row_idx, col_idx_base + 2, commit_link, self._xlsx_cellform_link, e.commit_subject)
							ws.write_string(row_idx, col_idx_base + 3, e.commit_body)
							first_hit = False
						ws.write_string(row_idx, col_idx, 'X')
					col_idx += 1
				if not first_hit :
					row_idx += 1
		
	def _write_report(self) :
		if self.xlsx_enabled :
			self._workbook = xlsxwriter.Workbook(self.xlsx_abspath)
			self._xlsx_cellform_rotate_m90 = self._workbook.add_format()
			self._xlsx_cellform_rotate_m90.set_rotation(-90)
			self._xlsx_cellform_rotate_m90.set_align('top')
			self._xlsx_cellform_link = self._workbook.add_format({'color': 'blue', 'underline': 1})
		self._write_a_environment_sheet()
		self._write_a_summary_sheet()
		for ws in self.sheet_lst :
			self._write_a_result_sheet(ws)
		
		if self.xlsx_enabled :
			self._workbook.close()

	def update_report(self):
		self._load_config()
		self._mark_to_sheet_data()
		self._write_report()
		
		

if __name__ == '__main__' :
	parser = argparse.ArgumentParser(description = 'Report pick upped Git-log into a XLSX file')
	parser.add_argument('--config', type=str, help='configuration file path (default: gitlog2xlsx.conf)')
	parser.add_argument('--debug', action='store_true', help='enable debug output to stderr')
	parser.add_argument('--git', type=str, help='git mirror directory, override to configuration file')
	parser.add_argument('--range', type=str, help='revision range string (default: None)')
	parser.add_argument('--since', type=str, help='altanative since date string (default: None)(e.g. : 1 weeks ago)')
	parser.add_argument('--until', type=str, help='altanative until date string (default: None)')
	parser.add_argument('--xlsx', type=str, help='xlsx output file path')
	parser.add_argument('--prjpath', type=str, help='project path')
	arg_dict = vars(parser.parse_args() )
	
	reporter = G2XReporter(arg_dict)
	reporter.update_report()
