import { Component, ElementRef, Input, OnInit, ViewChild } from '@angular/core';

import * as ace from 'ace-builds';
import 'ace-builds/src-noconflict/mode-json';
import 'ace-builds/src-noconflict/theme-github';

const THEME = 'ace/theme/github';
const LANG = 'ace/mode/json';

@Component({
  selector: 'app-editor',
  templateUrl: './editor.component.html',
  styleUrls: ['./editor.component.scss']
})
export class EditorComponent implements OnInit {

  @Input() public title: string;
  @ViewChild('editor', { static: true }) editorRef: ElementRef;
  private codeEditor: ace.Ace.Editor;

  constructor() { }

  ngOnInit(): void {
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

}
