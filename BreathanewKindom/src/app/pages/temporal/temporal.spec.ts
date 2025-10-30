import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Temporal } from './temporal';

describe('Temporal', () => {
  let component: Temporal;
  let fixture: ComponentFixture<Temporal>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Temporal]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Temporal);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
