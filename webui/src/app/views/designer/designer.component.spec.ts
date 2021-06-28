import { Component, Input } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CanvasComponent } from 'src/app/components/canvas/canvas.component';
import { EditorComponent } from 'src/app/components/editor/editor.component';

import { DesignerComponent } from './designer.component';

@Component({ selector: 'app-canvas', template: '' })
class CanvasComponentStub implements Partial<CanvasComponent> { }

@Component({ selector: 'app-editor', template: '' })
class EditorComponentStub implements Partial<EditorComponent> {
  @Input() title: string;
}

describe('DesignerComponent', () => {
  let component: DesignerComponent;
  let fixture: ComponentFixture<DesignerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [DesignerComponent, CanvasComponentStub, EditorComponentStub]
    })
      .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DesignerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
