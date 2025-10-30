import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { SoloNumerosDirective } from '../../directives/register/solo-numeros-code';

@Component({
  selector: 'app-auth-code',
  standalone: true,
  imports: [FormsModule, RouterModule, SoloNumerosDirective],
  templateUrl: './auth-code.html',
  styleUrl: './auth-code.css'
})
export class AuthCode {

}
