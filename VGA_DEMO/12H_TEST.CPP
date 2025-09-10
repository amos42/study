#include <stdio.h>
#include <dos.h>
#include <conio.h>
#include <stdlib.h>
#include <io.h>
#include "vga_reg.h"


char *vram = (char *)0xA0000000; // VGA 메모리 시작 주소

// 화면 모드를 설정한다
void set_screen_mode(int mode)
{
    union REGS regs;
    regs.h.ah = 0x00;
    regs.h.al = mode;
    int86(0x10, &regs, &regs);
}

void set_plane_mask(int plane_mask)
{
    outportb(SA_INDEX, SA_PLANE_MASK);
    outportb(SA_DATA, plane_mask);
}

void select_plane(int plane)
{
    set_plane_mask(1 << plane);
}

void set_write_mode(int mode)
{
    outportb(GC_INDEX, GC_MODE);
    outportb(GC_DATA, inportb(GC_DATA) & 0xFC | mode);
}

void set_write_func(int op_mode)
{
    outportb(GC_INDEX, GC_FUNC);
    outportb(GC_DATA, inportb(GC_FUNC) & 0xE7 | (op_mode << 3));
}

// 비트마스크 레지스터 설정
void set_bitmask(unsigned char mask)
{
    outportb(GC_INDEX, GC_BITMASK);
    outportb(GC_DATA, mask);
}

void set_enable_set_reset_mask(int plane_mask)
{
    outportb(GC_INDEX, GC_ENABLE_SET_RESET);
    outportb(GC_DATA, plane_mask);
}

void set_one_pixel_mode()
{
    set_plane_mask(0xF);
    set_write_mode(3);
    set_enable_set_reset_mask(0xF);
}

void set_pallete( int color, char red, char green, char blue )
{
    outportb(DAC_INDEX, color & 0xFF);
    outportb(DAC_DATA, red);
    outportb(DAC_DATA, green);
    outportb(DAC_DATA, blue);
}

void set_pallete_multi( int start_color, int count,
                        char *red, char *green, char *blue )
{
    outportb(DAC_INDEX, start_color & 0xFF);
    for( int i = 0; i < count; i++ ){
        outportb(DAC_DATA, *red++);
        outportb(DAC_DATA, *green++);
        outportb(DAC_DATA, *blue++);
    }
}

void set_color(unsigned char color)
{
    outportb(GC_INDEX, GC_SET_RESET); // Set/Reset
    outportb(GC_DATA, color & 0x0F);  // Set color (0-15)
}

void put_pixel(int x, int y)
{
    unsigned short offset = y * (640/8) + (x >> 3);
    unsigned unsigned char mask = (unsigned char)0x80 >> (x & 0x07);

    volatile char dummy = vram[offset]; // latch를 채우기 위한 더미 읽기 동작
    vram[offset] = mask;  // 모드 3에서는 mask를 쓴다.
}

void clear_screen0(unsigned char color)
{
    int p;
    unsigned i;
    char bits;

    for( p = 0; p < 4; p++ ){
        set_plane_mask(1 << p);
        bits = ((color >> p) & 0x01) ? 0xFF : 0x00;
        for(i = 0; i < 640U/8*480; i++) {
            vram[i] = bits;
        }
    }
    set_plane_mask(0xF);
}

void fill_screen()
{
    unsigned i;

    // set_color(color);
    // set_write_mode(3);

    for(i = 0; i < 640U/8*480; i++) {
        vram[i] = 0xFF;  // 모드 3에서는 mask를 쓴다.
    }
}

void put_font8x16(int x, int y, unsigned char *font)
{
    int i;
    unsigned short offset = y * (640/8) + (x >> 3);
    int shift = (x & 0x07);

    // set_write_mode(3);

    if (shift == 0) {
        for(i = 0; i < 16; i++) {
            unsigned char bits = font[i];
            volatile register dummy = vram[offset]; // latch를 채우기 위한 더미 읽기 동작
            vram[offset] = bits;  // 모드 3에서는 mask를 쓴다.
            offset += (640/8);
        }
    } else {
        int shift2 = 8 - shift;
        for(i = 0; i < 16; i++) {
            unsigned char bits = font[i];
            volatile register dummy = vram[offset]; // latch를 채우기 위한 더미 읽기 동작
            vram[offset] = bits >> shift;  // 모드 3에서는 mask를 쓴다.
            dummy = vram[offset+1]; // latch를 채우기 위한 더미 읽기 동작
            vram[offset+1] = bits << shift2;  // 모드 3에서는 mask를 쓴다.
            offset += (640/8);
        }
    }

    // set_write_mode(0);
}

unsigned char fonts[94][16]; // '!' ~ '~' 문자 폰트 데이터

void put_char(int x, int y, char c)
{
    if (c < '!') return;
    c -= '!';
    put_font8x16(x, y, fonts[(unsigned char)c]);
}

void put_string(int x, int y, char *str)
{
    int x2 = x;
    char ch;
    while(ch = *str++) {
        if (ch == ' ') {
            x2 += 8;
        } else if (ch == '\n') {
            y += 16;
            x2 = x;
            str++;
        } else {
            put_char(x2, y, ch);
            x2 += 8;
        }
    }
}

void main()
{
    // 640x480, 16색 그래픽 모드
    set_screen_mode(0x12);

    set_one_pixel_mode();

    // for(int i = 0; i <= 0x0f; i++){
	// //for(int j = 0; j < 10; j++) {
    //     set_color(i);
	//     put_pixel(10 + i, 10 + i);
	//     put_pixel(10 + 0xF - i, 10 + i);
	// //}
    // }

    //set_color(14); // 노란색

    FILE (*fp) = fopen("eng_8x16.fnt", "rb");
    fread(fonts, 16, 94, fp);
    fclose(fp);

    set_color(1);
    fill_screen();

    set_color(14);
    put_char(2+32, 32, 'A');
    set_color(2);
    put_char(2+32+16, 32, 'B');
    set_color(3);
    put_char(2+32+32, 32, 'C');
    set_color(4);
    put_char(2+32+48, 32, 'D');
    set_color(5);
    put_char(2+32+64, 32, 'E');
    set_color(6);
    put_char(2+32+80, 32, 'F');

    FILE (*fp2) = fopen("test.txt", "r");
    int len = filelength(fileno(fp2));
    char *txt = (char *)malloc(len + 1);
    fread(txt, len, 1, fp2);
    txt[len] = '\0';
    fclose(fp2);
    set_color(15);
    put_string(2+32, 32+16, txt);
    //put_string(2+32, 32+16, "Hello, World! This is a test.");

    getch();

    set_color(7);
    fill_screen();

    set_color(0);
    put_char(32+1, 32+1, 'a');
    set_color(14);
    put_char(32, 32, 'a');
    set_color(2);
    put_char(32+16, 32, 'b');
    set_color(3);
    put_char(32+32, 32, 'c');
    set_color(4);
    put_char(32+48, 32, 'd');
    set_color(5);
    put_char(32+64, 32, 'e');
    set_color(6);
    put_char(32+80, 32, 'f');

    getch();

    // for(i = 0; i <= 0x0f; i++){
	// //for(j = 0; j < 10; j++) {
    //     set_color(15-i);
    //     put_pixel(10 + i, 10 + i);
	//     put_pixel(10 + 0xF - i, 10 + i);
	// //}
    // }
    // getch();

    // 텍스트 모드로 복귀    
    set_screen_mode(0x03);
}
