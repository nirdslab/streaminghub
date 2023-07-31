import { AfterViewInit, Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import loader from '@monaco-editor/loader';
import { templates, Datasource, Dataset, Analytic } from './templates';

@Component({
  selector: 'app-editor',
  templateUrl: './editor.component.html',
  styleUrls: ['./editor.component.scss']
})
export class EditorComponent implements OnInit, AfterViewInit {

  @ViewChild("editor", { static: false }) editorElement?: ElementRef;

  public selection: 'DATASET' | 'DATASOURCE' | 'ANALYTIC' = 'DATASET';

  public datasetSpec: Dataset = { ...templates.dataset };
  public datasourceSpec: Datasource = { ...templates.datasource };
  public analyticSpec: Analytic = { ...templates.analytic };

  constructor() {
  }

  ngOnInit(): void {
  }

  ngAfterViewInit(): void {
    loader.init().then(monaco => {
      monaco.languages.json.jsonDefaults.setDiagnosticsOptions({ validate: true, allowComments: false, schemas: [], enableSchemaRequest: true });
      let json = null;
      if (this.selection == "DATASET") {
        json = this.datasetSpec;
      } else if (this.selection == "DATASOURCE") {
        json = this.datasourceSpec;
      } else if (this.selection == "ANALYTIC") {
        json = this.analyticSpec;
      }
      monaco.editor.create(this.editorElement?.nativeElement, { value: JSON.stringify(json, undefined, 2), language: 'json' });
    });
  }

}
