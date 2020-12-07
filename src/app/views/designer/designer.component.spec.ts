import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CanvasComponent } from 'src/app/components/canvas/canvas.component';
import { EditorComponent } from 'src/app/components/editor/editor.component';

import { DesignerComponent } from './designer.component';

describe('DesignerComponent', () => {
  let component: DesignerComponent;
  let fixture: ComponentFixture<DesignerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [DesignerComponent, CanvasComponent, EditorComponent]
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
