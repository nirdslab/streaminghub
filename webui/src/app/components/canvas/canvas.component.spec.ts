import { DragDropModule } from '@angular/cdk/drag-drop';
import { Component, Input } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatCardModule } from '@angular/material/card';
import { WidgetComponent } from '../widget/widget.component';

import { CanvasComponent } from './canvas.component';

@Component({ selector: 'app-widget', template: '' })
class WidgetComponentStub implements Partial<WidgetComponent> {
  @Input() name: string;
}

describe('CanvasComponent', () => {
  let component: CanvasComponent;
  let fixture: ComponentFixture<CanvasComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [CanvasComponent, WidgetComponentStub],
      imports: [MatCardModule, DragDropModule]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CanvasComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
