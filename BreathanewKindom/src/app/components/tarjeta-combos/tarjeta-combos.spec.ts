import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TarjetaCombos } from './tarjeta-combos';

describe('TarjetaCombos', () => {
  let component: TarjetaCombos;
  let fixture: ComponentFixture<TarjetaCombos>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TarjetaCombos]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TarjetaCombos);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
