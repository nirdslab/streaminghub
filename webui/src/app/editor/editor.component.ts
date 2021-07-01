import { AfterViewInit, Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import loader from '@monaco-editor/loader';
import templates from './templates';

@Component({
  selector: 'app-editor',
  templateUrl: './editor.component.html',
  styleUrls: ['./editor.component.scss']
})
export class EditorComponent implements OnInit, AfterViewInit {

  @ViewChild("editor", { static: false }) editorElement?: ElementRef;

  constructor() {
  }

  ngOnInit(): void {
  }

  ngAfterViewInit(): void {
    loader.init().then(monaco => {
      monaco.languages.json.jsonDefaults.setDiagnosticsOptions({ validate: true, allowComments: false, schemas: [], enableSchemaRequest: true});
      monaco.editor.create(this.editorElement?.nativeElement, { value: JSON.stringify(templates.dataset, undefined, 2), language: 'json' });
    });
  }

}
