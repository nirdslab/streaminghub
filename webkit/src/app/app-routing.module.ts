import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { DesignerComponent } from './views/designer/designer.component';
import { MetadataComponent } from './views/metadata/metadata.component';

const routes: Routes = [
  {
    path: '',
    component: DesignerComponent
  },
  {
    path: 'metadata',
    component: MetadataComponent
  },
  {
    path: 'designer',
    component: DesignerComponent
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
