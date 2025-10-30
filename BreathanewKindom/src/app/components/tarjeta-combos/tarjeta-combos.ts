import { Component, OnInit, Input, OnChanges, SimpleChanges, ChangeDetectionStrategy, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { ProductosService, CombosInterface } from '../../services/home/productosService';
import { Router } from '@angular/router';

@Component({
  selector: 'app-tarjeta-combo',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tarjeta-combos.html',
  styleUrls: ['./tarjeta-combos.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TarjetaCombos implements OnInit, OnChanges, OnDestroy {
  @Input() combosExternos: CombosInterface[] = [];
  @Input() autoCargar: boolean = true;

  combos$: Observable<CombosInterface[]>;
  private combosSubject = new BehaviorSubject<CombosInterface[]>([]);
  private destroy$ = new Subject<void>();

  constructor(
    private productosService: ProductosService,
    private router: Router
  ) {
    this.combos$ = this.combosSubject.asObservable();
  }

  ngOnInit(): void {
    if (this.autoCargar && (!this.combosExternos || this.combosExternos.length === 0)) {
      this.cargarCombos();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['combosExternos'] && changes['combosExternos'].currentValue) {
      const combos = Array.isArray(changes['combosExternos'].currentValue)
        ? changes['combosExternos'].currentValue
        : [];
      this.combosSubject.next(combos);
    }
  }

  private cargarCombos() {
    this.productosService.get_all_combos()
      .pipe(takeUntil(this.destroy$))
      .subscribe(combos => {
        this.combosSubject.next(combos);
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }


  personalizar_plato(id_producto: string, tipo: string, destino: string) {
    this.router.navigate(["/general"], {
      queryParams: {
        id_producto: id_producto,  // lo convertimos en string "id1" que luego se convierte en array
        tipo: tipo,
        destino: destino,
        accion: "personalizar_plato"
      }
    });
  }


}
