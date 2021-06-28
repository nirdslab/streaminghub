import { Component, Input } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { EditorComponent } from 'src/app/components/editor/editor.component';
import { MetadataFormComponent } from 'src/app/components/metadata-form/metadata-form.component';

import { MetadataComponent } from './metadata.component';

@Component({ selector: 'app-metadata-form', template: '' })
class MetadataFormComponentStub implements Partial<MetadataFormComponent> { }

@Component({ selector: 'app-editor', template: '' })
class EditorComponentStub implements Partial<EditorComponent> {
  @Input() title: string;
}

describe('MetadataComponent', () => {
  let component: MetadataComponent;
  let fixture: ComponentFixture<MetadataComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MetadataComponent, MetadataFormComponentStub, EditorComponentStub]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(MetadataComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
