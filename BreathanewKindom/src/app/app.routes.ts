import { Routes } from '@angular/router';
import { Home } from './pages/home/home';
import { Carrito } from './pages/carrito/carrito';
import { User } from './pages/user/user';
import { Login } from './pages/login/login';
import { Register } from './pages/register/register';
import { AuthCode } from './pages/auth-code/auth-code';
import { AuthError } from './pages/auth-error/auth-error';
import { Temporal } from './pages/temporal/temporal';
import { Result } from './pages/result/result';
import { DireccionPago } from './pages/direccion-pago/direccion-pago';
import { General } from './pages/general/general';
import { ResumenPedido } from './pages/resumen-pedido/resumen-pedido';

export const routes: Routes = [
    { path: '', component: Home },
    { path: 'carrito', component: Carrito },
    { path: 'usuario', component: User },
    { path: 'login', component: Login },
    { path: 'register', component: Register },
    { path: 'auth-code', component: AuthCode },
    { path: 'auth-error', component: AuthError },
    { path: 'result', component: Result },
    { path: 'direccion-pago', component: DireccionPago },
    { path: 'general', component: General },
    { path: 'resumen-pedido', component: ResumenPedido },


    { path: 'temporal', component: Temporal }
];
