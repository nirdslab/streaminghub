import { ComponentFixture, TestBed } from '@angular/core/testing';
import { EditorComponent } from 'src/app/components/editor/editor.component';
import { MetadataFormComponent } from 'src/app/components/metadata-form/metadata-form.component';

import { MetadataComponent } from './metadata.component';

describe('MetadataComponent', () => {
  let component: MetadataComponent;
  let fixture: ComponentFixture<MetadataComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [MetadataComponent, MetadataFormComponent, EditorComponent]
    })
      .compileComponents();
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
