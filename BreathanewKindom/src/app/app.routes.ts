import { Routes } from '@angular/router';
import { Home } from './pages/home/home';
import { Carrito } from './pages/carrito/carrito';
import { Favoritos } from './pages/favoritos/favoritos';
import { User } from './pages/user/user';
import { Login } from './pages/login/login';

export const routes: Routes = [
    { path: '', component: Home },
    { path: 'carrito', component: Carrito },
    { path: 'favoritos', component: Favoritos },
    { path: 'usuario', component: User },
    { path: 'login', component: Login }
];
