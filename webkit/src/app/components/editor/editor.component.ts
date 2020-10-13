import { Component, ElementRef, Input, OnInit, ViewChild } from '@angular/core';

import * as ace from 'ace-builds';
import 'ace-builds/src-noconflict/mode-json';
import 'ace-builds/src-noconflict/theme-github';
import { MetaStream } from '../metadata-form/metadata-form.component';

const THEME = 'ace/theme/github';
const LANG = 'ace/mode/json';

@Component({
  selector: 'app-editor',
  templateUrl: './editor.component.html',
  styleUrls: ['./editor.component.scss']
})
export class EditorComponent implements OnInit {

  @Input() public title: string;
  @ViewChild('editor', { static: true }) private editorRef: ElementRef;
  private codeEditor: ace.Ace.Editor;

  constructor() { }

  ngOnInit(): void {
    ace.config.set('workerPath', 'assets');
    const element = this.editorRef.nativeElement;
    const editorOptions: Partial<ace.Ace.EditorOptions> = {
      highlightActiveLine: true,
      fontSize: 12,
    };
    this.codeEditor = ace.edit(element, editorOptions);
    this.codeEditor.setTheme(THEME);
    this.codeEditor.getSession().setMode(LANG);
    this.codeEditor.setShowFoldWidgets(true);
  }

  update(metadata: MetaStream) {
    this.codeEditor.setValue(JSON.stringify(metadata, null, 2));
  }

}
