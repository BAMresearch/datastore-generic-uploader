#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author:      "Bastian Ruehle"
# @copyright:   "Copyright 2025, Bastian Ruehle, Federal Institute for Materials Research and Testing (BAM)"
# @version:     "1.0.0"
# @maintainer:  "Bastian Ruehle"
# @email        "bastian.ruehle@bam.de"

import tkinter as tk
import tkinter.filedialog as fd
import tkinter.messagebox as mb
import tkinter.ttk as ttk
from idlelib.tooltip import Hovertip

from typing import Union, Tuple, List, Dict, Optional
import os.path
import json
import threading
from datetime import datetime

from pybis import Openbis  # See https://pypi.org/project/PyBIS/

import Parser.DLSParser
import Parser.IRParser
import Parser.NMRParser
import Parser.SEMParser
import Parser.SpectramaxParser
import Parser.TEMParser


class GUI:
    """
    GUI class for the OpenBISUploadHelper.

    Parameters
    ----------
    master: Optional[tk.Tk] = None
        The Tk master window.
    """

    ExperimentalStepToInstrumentPermIDsMapping = {
        'EXPERIMENTAL_STEP.DLS': '20240514175804717-3108',          # ZETASIZER_ULTRA_RED
        'EXPERIMENTAL_STEP.PLATEREADER': '20240514180732941-3109',  # SPECTRAMAX_M3
    }

    UsernameToSpaceMapping = {
        'user1': '1.0 user1',
        'user2': '1.0 user2',
    }

    UsernameToProjectsMapping = {
        'user1': 'Project 1',
        'user2': 'Project 2',
        'all': ['Common Project 1', 'Common Project 2'],
    }

    def __init__(self, master: Optional[tk.Tk] = None) -> None:
        """
        GUI class for the OpenBISUploadHelper.

        Parameters
        ----------
        master: Optional[tk.Tk] = None
            The Tk master window.
        """
        self.create_preview = tk.IntVar(value=1)
        self.create_metadata = tk.IntVar(value=0)
        self.upload_to_openbis = tk.IntVar(value=1)

        self.o: Union[None, Openbis] = None
        self.OPENBIS_URL = 'https://main.datastore.bam.de/'

        x_startup = 200
        y_startup = 100
        pad_x = 4
        pad_y = 4
        textbox_minwidth = 50

        if master is None:
            master = tk.Tk()
        self.master = master

        self.master.resizable(True, True)
        self.master.title('OpenBIS Upload Helper')
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=2)
        self.master.columnconfigure(2, weight=1)

        # build ui
        # Export Options
        self.export_options_frame = ttk.Labelframe(self.master)
        self.export_options_frame.configure(
            labelanchor="nw", relief="sunken", text="Export Options"
        )
        self.export_options_frame.grid(padx=pad_x, pady=pad_y, column=0, columnspan=3, row=0, rowspan=1, sticky="ew")
        self.export_options_frame.columnconfigure(0, weight=0)
        self.export_options_frame.columnconfigure(1, weight=1)
        self.export_options_frame.columnconfigure(2, weight=0)

        self.filenames_label = ttk.Label(self.export_options_frame)
        self.filenames_label.configure(anchor="w", text="Files:")
        self.filenames_label.grid(padx=pad_x, pady=pad_y, column=0, row=0, sticky='ew')

        self.filenames_textbox = ttk.Entry(self.export_options_frame,
                                           width=textbox_minwidth)
        self.filenames_textbox.insert("end", os.path.expanduser('~'))
        self.filenames_textbox.grid(padx=pad_x, pady=pad_y, column=1, columnspan=1, row=0, sticky='ew')

        self.file_chooser = ttk.Button(self.export_options_frame)
        self.file_chooser.configure(
            text="...", width=2, command=self.choose_files
        )
        self.file_chooser.grid(padx=pad_x, pady=pad_y, column=2, columnspan=1, row=0)

        self.create_preview_checkbox = ttk.Checkbutton(self.export_options_frame)
        self.create_preview_checkbox.configure(
            text="Create Preview Image", variable=self.create_preview
        )
        self.create_preview_checkbox.grid(padx=pad_x, pady=pad_y, column=0, columnspan=3, row=1, sticky='ew')

        self.create_metadata_checkbox = ttk.Checkbutton(self.export_options_frame)
        self.create_metadata_checkbox.configure(
            text="Create Metadata File", variable=self.create_metadata
        )
        self.create_metadata_checkbox.grid(padx=pad_x, pady=pad_y, column=0, columnspan=3, row=2, sticky='ew')

        self.upload_to_openbis_checkbox = ttk.Checkbutton(self.export_options_frame)
        self.upload_to_openbis_checkbox.configure(
            text="Upload to OpenBIS", variable=self.upload_to_openbis, command=self.toggle_openbis_options_enable
        )
        self.upload_to_openbis_checkbox.grid(padx=pad_x, pady=pad_y, column=0, columnspan=3, row=3, sticky='ew')

        # OpenBIS Options
        self.openbis_options_frame = ttk.Labelframe(self.master)
        self.openbis_options_frame.configure(
            labelanchor="nw", relief="sunken", text="OpenBIS Options"
        )
        self.openbis_options_frame.grid(padx=pad_x, pady=pad_y, column=0, columnspan=3, row=1, rowspan=1, sticky="ew")
        self.openbis_options_frame.columnconfigure(0, weight=0)
        self.openbis_options_frame.columnconfigure(1, weight=1)
        self.openbis_options_frame.columnconfigure(2, weight=0)

        self.user_name_label = ttk.Label(self.openbis_options_frame)
        self.user_name_label.configure(anchor="w", text="User Name (LDAP):")
        self.user_name_label.grid(padx=pad_x, pady=pad_y, column=0, row=0, sticky='ew')

        self.user_name_textbox = ttk.Entry(self.openbis_options_frame, validatecommand=self.user_name_val, validate='focusout')
        self.user_name_textbox.grid(padx=pad_x, pady=pad_y, column=1, row=0, sticky='ew')

        self.password_label = ttk.Label(self.openbis_options_frame)
        self.password_label.configure(
            anchor="w", text="Password (LDAP):"
        )
        self.password_label.grid(padx=pad_x, pady=pad_y, column=0, row=1, sticky='ew')

        self.password_textbox = ttk.Entry(self.openbis_options_frame, show='*')
        self.password_textbox.grid(padx=pad_x, pady=pad_y, column=1, row=1, sticky='ew')

        self.space_name_label = ttk.Label(self.openbis_options_frame)
        self.space_name_label.configure(
            anchor="w", text="Space Name:"
        )
        self.space_name_label.grid(padx=pad_x, pady=pad_y, column=0, row=2, sticky='ew')

        self.space_name_combobox = ttk.Combobox(self.openbis_options_frame, values=[i for i in self.UsernameToSpaceMapping.values()])
        self.space_name_combobox.grid(padx=pad_x, pady=pad_y, column=1, row=2, sticky='ew')

        self.project_name_label = ttk.Label(self.openbis_options_frame)
        self.project_name_label.configure(
            anchor="w", text="Project Name:"
        )
        self.project_name_label.grid(padx=pad_x, pady=pad_y, column=0, row=3, sticky='ew')

        self.project_name_combobox = ttk.Combobox(self.openbis_options_frame, values=[i for i in self.UsernameToProjectsMapping.values() if isinstance(i, str)] + [j for i in self.UsernameToProjectsMapping.values() for j in i if not isinstance(i, str)])
        self.project_name_combobox.grid(padx=pad_x, pady=pad_y, column=1, row=3, sticky='ew')

        self.experiment_name_label = ttk.Label(self.openbis_options_frame)
        self.experiment_name_label.configure(
            anchor="w", text="Experiment Name:"
        )
        self.experiment_name_label.grid(padx=pad_x, pady=pad_y, column=0, row=4, sticky='ew')

        self.experiment_name_textbox = ttk.Entry(self.openbis_options_frame)
        self.experiment_name_textbox.grid(padx=pad_x, pady=pad_y, column=1, row=4, sticky='ew')

        # Export Button
        self.upload_button = ttk.Button(self.master)
        self.upload_button.configure(
            text="Export", width=20, command=self.export
        )
        self.upload_button.grid(padx=pad_x, pady=pad_y, column=0, row=3, sticky='w')

        # Status Bar
        self.status_bar = ttk.Label(self.master)
        self.status_bar.configure(anchor="w", text="Status: Idle")
        #self.status_bar.grid(padx=pad_x, pady=pad_y, column=1, row=3, sticky='ew')

        # Progress Bar
        self.progress_bar = ttk.Progressbar(self.master)
        self.progress_bar.configure(
            orient='horizontal', mode='indeterminate'
        )
        #self.progress_bar.grid(padx=pad_x, pady=pad_y, column=2, row=3, sticky='ew')

        self.toggle_openbis_options_enable()

        # Let Tkinter calculate window size based on widgets
        self.master.update_idletasks()
        # Get current window size
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        # Set window position (x=300, y=200) with current size
        self.master.geometry(f"{width}x{height}+{x_startup}+{y_startup}")

    def run(self) -> None:
        """Run the mainloop"""
        self.master.mainloop()

    def choose_files(self) -> None:
        """Callback for file chooser dialogue"""
        current_dir = self.filenames_textbox.get()
        self.filenames_textbox.delete(0, "end")
        self.filenames_textbox.insert("end", ';'.join(fd.askopenfilenames(filetypes=(('All Files', '*'), ('Electron Microscopy Files', 'emd tif dm3'), ('NMR Files', 'jdx dx'), ('IR Files', 'spa csv'), ('Plate Reader Files', 'spa spd csv')), title='Select Files for Upload...', initialdir=current_dir)))

    def toggle_openbis_options_enable(self) -> None:
        """Toggle the state of the widgets related to OpenBIS"""
        if self.upload_to_openbis.get():
            state = 'normal'
        else:
            state = 'disabled'

        for child in self.openbis_options_frame.winfo_children():
            child.configure(state=state)

    def user_name_val(self) -> bool:
        """Callback after user_name validation, used to set default values for other fields based on entered username"""
        user_name = self.user_name_textbox.get()
        if len(user_name) < 1:
            return False
        if user_name in self.UsernameToSpaceMapping.keys():
            self.space_name_combobox.delete(0, tk.END)
            self.space_name_combobox.insert(tk.END, self.UsernameToSpaceMapping[user_name])

        if user_name in self.UsernameToProjectsMapping.keys():
            self.project_name_combobox.delete(0, tk.END)
            self.project_name_combobox.insert(tk.END, self.UsernameToProjectsMapping[user_name])

        return True

    def export(self) -> None:
        """Callback for export button. Runs exporter in a new thread."""
        t = threading.Thread(target=self.run_export)
        t.start()

    def write_characterization_step(self, space_name: str, project_name: str, experiment_name: str, experimental_step_type: str, files: Union[str, list, tuple], metadata: dict[str, Union[str, float, int]]) -> bool:
        """
        Uploads the provided files to OpenBIS and sets the corresponding metadata.

        Parameters
        ----------
        space_name: str
            The OpenBIS Space Name to which the data is uploaded.
        project_name: str
            The OpenBIS Project Name to which the data is uploaded.
        experiment_name: str
            The OpenBIS Experiment Name to which the data is uploaded. If the experiment does not exist yet, it is created.
        experimental_step_type: str
            The OpenBIS Experimental Step Type of the Data.
        files: Union[str, list, tuple]
            The list of files that are uploaded.
        metadata: dict[str, Union[str, float, int]]
            The dictionary with metadata for the experimental step.

        Returns
        -------
        bool
            True if successful.
        """

        timestamp = str(datetime.now())
        timestamp = timestamp[:timestamp.rfind('.')].replace(' ', '_').replace(':', '-')

        if files is None:
            files = []
        elif isinstance(files, str):
            files = [files]

        # Get the project object from the project name
        for project in self.o.get_projects(space=space_name.upper().replace(' ', '_')):
            if project.code.lower() == project_name.lower().replace(' ', '_'):
                break
        else:
            mb.showerror("Exporter", f'Project "{project_name}" not found in Space "{space_name}"')
            return False

        # Get the experiment object from the experiment name (or create it if it doesn't exist)
        for experiment in project.get_experiments():
            if experiment.props['$name'] == experiment_name:
                break
        else:
            # Create a new one if nothing is found
            experiment_code = f"{experiment_name.upper().replace(' ', '_').replace(':', '-')}-{timestamp}"
            experiment = self.o.new_experiment(
                code=experiment_code,
                type='DEFAULT_EXPERIMENT',
                project=project,
                props={"$name": f"{experiment_name}"}
            )
            experiment.save()

        # Create a new experimental step object in this experiment
        if experimental_step_type in self.ExperimentalStepToInstrumentPermIDsMapping.keys():
            parents = [self.ExperimentalStepToInstrumentPermIDsMapping[experimental_step_type]]
        else:
            parents = []

        experimental_step_code = f'{experimental_step_type}-{timestamp}'
        experimental_step_name = f'{experimental_step_type[experimental_step_type.rfind(".")+1:]}_{experiment_name}'
        experimental_step = self.o.new_object(
            code=experimental_step_code,
            type=experimental_step_type,
            experiment=experiment,
            parents=parents,
            props={"$name": f"{experimental_step_name}"}
        )
        experimental_step.save()

        # Add files as a dataset
        for i, file in enumerate(files):
            self.status_bar.configure(text=f'Uploading file {i+1}/{len(files)}: {file}...')
            file_path = os.path.abspath(file)
            dataset_characterization_file = self.o.new_dataset(
                type='RAW_DATA',
                experiment=experiment,
                sample=experimental_step,
                files=file_path,
                props={"$name": os.path.basename(os.path.splitext(file_path)[0]), "notes": "Raw Data"}
            )
            dataset_characterization_file.save()

        # Upload the preview image (if available)
        for file in os.listdir(os.path.dirname(files[0])):
            self.status_bar.configure(text=f'Uploading preview image...')
            file_path = os.path.abspath(os.path.join(os.path.dirname(files[0]), file))
            if file.endswith('preview.png'):
                dataset_characterization_file = self.o.new_dataset(
                    type='ELN_PREVIEW',
                    experiment=experiment,
                    sample=experimental_step,
                    files=file_path,
                    props={"$name": os.path.basename(os.path.splitext(file_path)[0]), "notes": "Preview Image"}
                )
                dataset_characterization_file.save()
                break

        # Fill the metadata fields (if metadata is available)
        if metadata is not None and metadata != '' and metadata != {}:
            self.status_bar.configure(text='Setting metadata fields...')
            experimental_step.set_properties({k.lower(): v for k, v in metadata.items()})
            experimental_step.save()
        return True

    def run_export(self) -> None:
        """
        Run the exporter that determines the file type, passes the files to the corresponding parser, and calls a method for uploading the data and metadata to OpenBIS.
        """
        try:
            self.status_bar.grid(padx=4, pady=4, column=1, row=3, sticky='ew')
            self.progress_bar.grid(padx=4, pady=4, column=2, row=3, sticky='ew')
            self.progress_bar.start()

            # Try to determine the file type
            files = self.filenames_textbox.get().split(';')
            extensions = [os.path.splitext(i)[1].lower() for i in files]
            self.status_bar.configure(text='Analyzing file types...')
            if any([i == '.dm3' or i == '.emd' for i in extensions]):
                parse_data = Parser.TEMParser.parse_tem
                experimental_step_type = 'EXPERIMENTAL_STEP.TEM'
            elif any([i == '.tif' or i == '.tiff' for i in extensions]):
                for file in files:
                    if file.endswith('.tif') or file.endswith('.tiff'):
                        with open(files[0], "rb") as f:
                            h = f.read(16)
                        break
                if h[0x08] == 0x12 and h[0x09] == 0x00 and h[0x0A] == 0xFE:
                    parse_data = Parser.SEMParser.parse_sem
                    experimental_step_type = 'EXPERIMENTAL_STEP.SEM'
                else:
                    parse_data = Parser.TEMParser.parse_tem
                    experimental_step_type = 'EXPERIMENTAL_STEP.TEM'
            elif any([i == '.jdx' or i == '.jx' or i == '.jcamp' or i == '.fid' for i in extensions]):
                parse_data = Parser.NMRParser.parse_nmr
                experimental_step_type = 'EXPERIMENTAL_STEP.NMR'
            elif any([i == '.spa' for i in extensions]):
                parse_data = Parser.IRParser.parse_ir
                experimental_step_type = 'EXPERIMENTAL_STEP.FTIR'
            elif any([i == '.sda' or i == '.spr' or i == '.txt' for i in extensions]):
                parse_data = Parser.SpectramaxParser.parse_platerader
                experimental_step_type = 'EXPERIMENTAL_STEP.PLATEREADER'
            elif any([i == '.csv' for i in extensions]):
                fc = []
                for file in files:
                    if file.endswith('.csv'):
                        fc = [i for i in open(file, 'r')]
                        break
                if fc[0].startswith('Datapoints for Distributions'):
                    parse_data = Parser.DLSParser.parse_dls
                    experimental_step_type = 'EXPERIMENTAL_STEP.DLS'
                else:
                    parse_data = Parser.IRParser.parse_ir
                    experimental_step_type = 'EXPERIMENTAL_STEP.FTIR'
            else:
                mb.showinfo("Parser", "Could not find suitable parser for the selected file(s)")
                return

            # Parse the data
            self.status_bar.configure(text='Parsing data...')
            metadata = parse_data(files=self.filenames_textbox.get().split(';'), create_preview=bool(self.create_preview.get()))
            if metadata != {}:
                if not self.upload_to_openbis.get():
                    mb.showinfo("Parser", "Export finished successfuly.\nData were not uploaded to OpenBIS.")
            else:
                mb.showerror("Parser", "Error while parsing files.")
                return

            if self.create_metadata.get():
                json.dump(metadata, open(f'{os.path.splitext(files[0])[0]}.md', 'w'), indent=4, ensure_ascii=False)

            # Upload to openbis
            if self.upload_to_openbis.get():
                self.status_bar.configure(text='Logging into OpenBIS...')
                if self.o is None:
                    self.o = Openbis(url=self.OPENBIS_URL, verify_certificates=False)
                if not self.o.is_session_active():
                    self.o.login(username=self.user_name_textbox.get(), password=self.password_textbox.get())

                experiment_name = self.experiment_name_textbox.get()
                project_name = self.project_name_combobox.get()
                space_name = self.space_name_combobox.get()

                if self.write_characterization_step(space_name=space_name, project_name=project_name, experiment_name=experiment_name, experimental_step_type=experimental_step_type, files=files, metadata=metadata):
                    self.status_bar.configure(text='Done.')
                    # mb.showinfo("Exporter", "Done.")
                else:
                    mb.showerror("Exporter", "Error while uploading data to OpenBIS.")
        except Exception as ex:
            mb.showerror("Exporter", str(ex))
        finally:
            self.progress_bar.stop()
            self.progress_bar.grid_forget()
            self.status_bar.grid_forget()
            if self.o is not None:
                self.o.logout()


if __name__ == '__main__':
    root = tk.Tk()
    app = GUI(root)
    app.run()
