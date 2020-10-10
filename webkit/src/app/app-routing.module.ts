import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { DesignerComponent } from './views/designer/designer.component';

const routes: Routes = [
  {
    path: '',
    component: DesignerComponent
  },
  {
    path: 'metadata',
    component: DesignerComponent
  },
  {
    path: 'pipelines',
    component: DesignerComponent
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
