import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth/auth-service';
import { response } from 'express';
import { error } from 'console';

@Component({
  selector: 'app-login',
  imports: [],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class Login {
  usuario = '';
  contraseña = '';

  constructor(private authservice: AuthService, private router: Router) { }

  onLogin(): void {
    this.authservice.login(this.usuario, this.contraseña).subscribe({
      next: (response) => {
        console.log('Login exitoso', response)

        localStorage.setItem('token', response.token);

        this.router.navigate(['']);
      },
      error: (error) => {
        console.error('Error al iniciar sesion', error);
        alert('Usuario o contraseña incorrectos');
      }
    });
  }

}
