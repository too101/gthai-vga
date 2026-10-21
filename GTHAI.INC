;======================================================================
; Include file for GTHAI.COM
; Contents:     EQUATES
;               MACROS
; Build with JWasm and build.ps1 (raw binary font inclusion required).
;======================================================================
IFDEF __JWASM__
OPTION NOSCOPED
ELSE
JUMPS
LOCALS
ENDIF

IFDEF CPU_386
.386
ELSE
.8086
ENDIF

VERSION_ID = 330
VERSION_STRING MACRO
IFDEF CPU_386
        DB '3.30 (386)'
ELSE
        DB '3.30 (G)'
ENDIF
ENDM
VERSION_ENCODED MACRO
IFDEF CPU_386
    DB _3,_PERIOD,_3,_0,_SPACE,_LEFT_PAREN,_3,_8,_6,_RIGHT_PAREN
ELSE
    DB _3,_PERIOD,_3,_0,_SPACE,_LEFT_PAREN,_G,_RIGHT_PAREN
ENDIF
ENDM

COMMENT *
;======================================================================
;       REVISION HISTORY
;  Revision     Date            Description
;======================================================================
     3.00(G)    1/17/92         Disassemble VTHAI, create source, and
                                add IBM Proprinter support.

     3.01(G)    6/23/92         Upper print row not spacing correctly.

     3.02(G)    7/16/92         Revised variable spacing routines to
                                proportionately distribute steps among
                                top, middle, main, and bottom rows.

     3.03(G)    7/31/92         Reenable interrupts while processing
                                screen updates. Set TIMER_BUSY flag
                                to prevent reentrance.

     3.04(G)    9/15/92         Rewrite print routine to properly
                                calulate combined vowel fonts for
                                IBM printer. Also, send ESC 6 to 
                                enable printing of combined vowel
                                font characters on IBM.
                                Change display font character 0FBH
                                to check mark.

     3.05(G)    10/09/92        Enable automatic paper detection for
                                IBM 4722 printer (Parallel only).

     3.06(G)    03/09/93        Check command line for U and unload
                                GThai if it is resident and can be
                                unloaded. Give appropriate messages
                                otherwise.

     3.07(G)    12/12/93        Back out change from 3.03(G). Incomplete
                                screen repaint during application's 
                                interrupt handlers.

                                Get and Set interrupts via Int 21h
                                Functions 25h and 35h instead of direct
                                peek and poke. It's safer.

                                Also, turned on Turbo Assembler options
                                for jump optimization and local labels.

      3.08(G)   05/11/94        Reimplement change from 3.03(G). (Hopefully
                                better coded this time.) Reenable interrupts
                                at beginning of Int 8 before chaining old
                                Int 8. Then check TIMER_BUSY, exit if set,
                                set it, update video, clear it. This prevents
                                loss of other interrupts, such as serial
                                port handlers.


      3.09(G)   05/16/94        Adjust combined vowel offsets for Epson
                                printers. Brute force translate vowels:
                                SARA_O
                                SARA_MAI_MUAN
                                SARA_MAI_MALAI
                                Epson printer font differs from IBM on
                                these characters.

      3.10(G)   05/19/94        Pass BACKSPACE to printer unconditionally.
                                Previously passed only if previous AH was
                                not zero. This caused occasional hangs on
                                the IBM 4722, due to loading BACKSPACE chars
                                into the Thai print buffer until limit was
                                reached.

                                This change resolved the majority of the
                                printer hesitations; however, the 4722
                                sometimes does not return Out of Paper for
                                several seconds.

*       ;End comment

;======================================================================
; Program default settings
;======================================================================

;----------------------------------------------------------------------
; Print line spacing defaults
;----------------------------------------------------------------------
DFLT_TOP_LPI  = 7
DFLT_MDL_LPI  = 19
DFLT_MAIN_LPI = 19
DFLT_BTM_LPI  = 0

PRINT_BUF_MAX=200

;----------------------------------------------------------------------
; Settings for control panel
;----------------------------------------------------------------------
TITLE_COLOR = RED_BG+BRIGHT_WHITE
CELL_HEIGHT = 19
SCREEN_GLYPH_STRIDE = CELL_HEIGHT
GLYPH_WORDS = (CELL_HEIGHT+1)/2
GLYPH_COMPOSE_BYTES = GLYPH_WORDS*2
; Tone marks rest at rows 3..5; raise three rows only above an upper vowel.
TONE_RAISE = 3
CHAR_HEIGHT = CELL_HEIGHT+1
PANEL_FIELD_TOP = 54
PANEL_FIELD_STEP = CELL_HEIGHT+3

; DX is the option index (0..8); preserve AX for the caller.
PANEL_FIELD_POSITION MACRO
         PUSH AX
         MOV AX,PANEL_FIELD_STEP
         MUL DX
         MOV DX,AX
         POP AX
         ADD DX,PANEL_FIELD_TOP
ENDM

PANEL_LEFT_COLUMN = 48
PANEL_WIDTH = 544
PANEL_HEIGHT = (275*CELL_HEIGHT+13)/14
PANEL_TOP_ROW = (480-PANEL_HEIGHT+CHAR_HEIGHT)/2
PANEL_FRAME_WIDTH = 6
PANEL_EDGE_WIDTH = 2
PANEL_FRAME_COLOR = CYAN
PANEL_EDGE_COLOR =  BRIGHT_CYAN
PANEL_SHADOW_COLOR = BLACK
PANEL_BG_COLOR = GREY

;----------------------------------------------------------------------
; Settings for unload frame
;----------------------------------------------------------------------
UNLOAD_LEFT_COLUMN = 216
UNLOAD_TOP_ROW = (480-136+CHAR_HEIGHT)/2
UNLOAD_WIDTH = 200
UNLOAD_HEIGHT = 136
UNLOAD_FRAME_WIDTH = 6
UNLOAD_EDGE_WIDTH = 2
UNLOAD_FRAME_COLOR = CYAN
UNLOAD_EDGE_COLOR = BRIGHT_CYAN
UNLOAD_SHADOW_COLOR = BLACK
UNLOAD_BG_COLOR = BRIGHT_WHITE

;----------------------------------------------------------------------
;        Define common ASCII control codes.
;----------------------------------------------------------------------
BELL     EQU   7
BACKSPC  EQU   8
HT       EQU   9                 ;Tab character.
LF       EQU   10                ;Line feed character.
FORMFEED EQU   12                ;Form feed character.
CR       EQU   13                ;Carriage return character.
EOF      EQU   26                ;Typical end-of-file mark.
ESCAPE   EQU   01BH              ;ESCAPE char

;----------------------------------------------------------------------
; COLORS
;----------------------------------------------------------------------
BLACK = 0
BLACK_BG = BLACK SHL 4
BLUE = 1
BLUE_BG = BLUE SHL 4
GREEN = 2
GREEN_BG = GREEN SHL 4
CYAN = 3
CYAN_BG = CYAN SHL 4
RED = 4
RED_BG = RED SHL 4
VIOLET = 5
VIOLET_BG = VIOLET SHL 4
BROWN = 6
BROWN_BG = BROWN SHL 4
WHITE = 7
WHITE_BG = WHITE SHL 4
GREY = 8
GREY_BG = GREY SHL 4
BRIGHT_BLUE = 9
BRIGHT_BLUE_BG = BRIGHT_BLUE SHL 4
BRIGHT_GREEN = 10
BRIGHT_GREEN_BG = BRIGHT_GREEN SHL 4
BRIGHT_CYAN = 11
BRIGHT_CYAN_BG = BRIGHT_CYAN SHL 4
BRIGHT_RED = 12
BRIGHT_RED_BG = BRIGHT_RED SHL 4
BRIGHT_VIOLET = 13
BRIGHT_VIOLET_BG = BRIGHT_VIOLET SHL 4
YELLOW = 14
YELLOW_BG = YELLOW SHL 4
BRIGHT_WHITE = 15
BRIGHT_WHITE_BG = BRIGHT_WHITE SHL 4
;======================================================================
; KEYBOARD SCAN CODES
;======================================================================
SHIFT_STAT_NOSHIFT = 0
SHIFT_STAT_CTRL = 4
SHIFT_STAT_ALT = 8
SCAN_TILDE = 29H
;======================================================================
; DOS segment/offset equates
;======================================================================
INT_TBL_OFF_TIMER       = 8 * 4
INT_TBL_SEG_TIMER       = INT_TBL_OFF_TIMER + 2
INT_TBL_OFF_KBD         = 9 * 4
INT_TBL_SEG_KBD         = INT_TBL_OFF_KBD + 2
INT_TBL_OFF_VIDEO       = 10H * 4
INT_TBL_SEG_VIDEO       = INT_TBL_OFF_VIDEO + 2
INT_TBL_OFF_PRINTER     = 17H * 4
INT_TBL_SEG_PRINTER     = INT_TBL_OFF_PRINTER + 2
INT_TBL_OFF_VID_PARMS   = 1DH * 4
INT_TBL_SEG_VID_PARMS   = INT_TBL_OFF_VID_PARMS + 2
INT_TBL_OFF_CRIT_ERR    = 24H * 4
INT_TBL_SEG_CRIT_ERR    = INT_TBL_OFF_CRIT_ERR + 2
;======================================================================
; BIOS segment/offset equates
;======================================================================
BIOS_SEG = 40H
BIOS_EQUIPMENT_LIST = 10H
BIOS_SHIFT_STATUS = 17H
BIOS_KEYBOARD_HEAD_POINTER = 1AH
BIOS_KEYBOARD_TAIL_POINTER = 1CH
BIOS_KEYBOARD_BUFFER = 1EH
BIOS_DISPLAY_MODE = 49H
BIOS_CURSOR_ADDRESS = 50H     ;WORD POINTER
BIOS_CURSOR_COL_PG0 = 50H     ;BYTE POINTER
BIOS_CURSOR_ROW_PG0 = 51H     ;BYTE POINTER
BIOS_CURSOR_COL_PG1 = 52H
BIOS_CURSOR_ROW_PG1 = 53H
BIOS_CURSOR_COL_PG2 = 54H
BIOS_CURSOR_ROW_PG2 = 55H
BIOS_CURSOR_COL_PG3 = 56H
BIOS_CURSOR_ROW_PG3 = 57H
BIOS_CURSOR_COL_PG4 = 58H
BIOS_CURSOR_ROW_PG4 = 59H
BIOS_CURSOR_COL_PG5 = 5AH
BIOS_CURSOR_ROW_PG5 = 5BH
BIOS_CURSOR_COL_PG6 = 5CH
BIOS_CURSOR_ROW_PG6 = 5DH
BIOS_CURSOR_COL_PG7 = 5EH
BIOS_CURSOR_ROW_PG7 = 5FH
BIOS_MODE_CONTROL_REG = 65H
;----------------------------------------------------------------------
; VIDEO (INT 10H) Functions
;----------------------------------------------------------------------
VID_SETMODE = 0
TEXT_80X25 = 3
VID_SET_CURSOR_POS = 2
VID_READ_CURSOR_POS_SIZE = 3
SCREEN_SIZE = 2000  ;80 X 25
;----------------------------------------------------------------------
; KEYBOARD (INT 16H) FUNCTIONS
;----------------------------------------------------------------------
KBD_READ             = 0
KBD_STATUS           = 1
KBD_GET_SHIFT_STATUS = 2
;----------------------------------------------------------------------
; DOS (INT 21H) Functions
;----------------------------------------------------------------------
DOS_PRINT_STRING = 9
DOS_OPEN_FILE = 3DH
O_RDRW = 2
DOS_CLOSE_FILE = 3EH
DOS_WRITE_HANDLE = 40H
DOS_FREE_MEMORY = 49H
DOS_TERMINATE = 4CH
;----------------------------------------------------------------------
; ASCII chars XOR 5
;----------------------------------------------------------------------
END_OF_STRING = 0 XOR 5

_SPACE = ' ' XOR 5
_EXCLAMATION = '!' XOR 5
_DOUBLE_QUOTE = '"' XOR 5
_POUND = '#' XOR 5
_DOLLAR = '$' XOR 5
_PERCENT = '%' XOR 5
_AMPERSAND = '&' XOR 5
_SINGLE_QUOTE = "'" XOR 5
_LEFT_PAREN = '(' XOR 5
_RIGHT_PAREN = ')' XOR 5
_STAR = '*' XOR 5
_PLUS = '+' XOR 5
_COMMA = ',' XOR 5
_HYPHEN = '-' XOR 5
_PERIOD = '.' XOR 5
_SLASH = '/' XOR 5
_0 = '0' XOR 5
_1 = '1' XOR 5
_2 = '2' XOR 5
_3 = '3' XOR 5
_4 = '4' XOR 5
_5 = '5' XOR 5
_6 = '6' XOR 5
_7 = '7' XOR 5
_8 = '8' XOR 5
_9 = '9' XOR 5
_COLON = ':' XOR 5
_SEMICOLON = ';' XOR 5
_LESSTHAN = '<' XOR 5
_EQUAL = '=' XOR 5
_GREATERTHAN = '>' XOR 5
_QUESTION = '?' XOR 5
_AT = '@' XOR 5
_A = 'A' XOR 5
_B = 'B' XOR 5
_C = 'C' XOR 5
_D = 'D' XOR 5
_E = 'E' XOR 5
_F = 'F' XOR 5
_G = 'G' XOR 5
_H = 'H' XOR 5
_I = 'I' XOR 5
_J = 'J' XOR 5
_K = 'K' XOR 5
_L = 'L' XOR 5
_M = 'M' XOR 5
_N = 'N' XOR 5
_O = 'O' XOR 5
_P = 'P' XOR 5
_Q = 'Q' XOR 5
_R = 'R' XOR 5
_S = 'S' XOR 5
_T = 'T' XOR 5
_U = 'U' XOR 5
_V = 'V' XOR 5
_X = 'X' XOR 5
_Y = 'Y' XOR 5
_Z = 'Z' XOR 5
_LEFT_BRACKET = '[' XOR 5
_BACKSLASH = '\' XOR 5
_RIGHT_BRACKET = ']' XOR 5
_CARET = '^' XOR 5
_UNDERBAR = '_' XOR 5
_LEFT_TICK = '`' XOR 5
a_ = 'a' XOR 5
b_ = 'b' XOR 5
c_ = 'c' XOR 5
d_ = 'd' XOR 5
e_ = 'e' XOR 5
f_ = 'f' XOR 5
g_ = 'g' XOR 5
h_ = 'h' XOR 5
i_ = 'i' XOR 5
j_ = 'j' XOR 5
k_ = 'k' XOR 5
l_ = 'l' XOR 5
m_ = 'm' XOR 5
n_ = 'n' XOR 5
o_ = 'o' XOR 5
p_ = 'p' XOR 5
q_ = 'q' XOR 5
r_ = 'r' XOR 5
s_ = 's' XOR 5
t_ = 't' XOR 5
u_ = 'u' XOR 5
v_ = 'v' XOR 5
w_ = 'w' XOR 5
x_ = 'x' XOR 5
y_ = 'y' XOR 5
z_ = 'z' XOR 5
_LEFT_CURLY = '{' XOR 5
_VERTICAL_BAR = '|' XOR 5
_RIGHT_CURLY = '}' XOR 5
_TILDE = '~' XOR 5

;======================================================================
; Thai character names
;======================================================================
        ;------------;
        ; Consonants ;
        ;------------;
THAI_SPACE      = 0A0H
KO_KAI          = 0A1H
KHO_KHAI        = 0A2H
KHO_KHUAT       = 0A3H
KHO_KHWAI       = 0A4H
KHO_KHON        = 0A5H
KHO_RAKHANG     = 0A6H
NGO_NGU         = 0A7H
CHO_CHAN        = 0A8H
CHO_CHING       = 0A9H
CHO_CHANG       = 0AAH
SO_SO           = 0ABH
CHO_CHOE        = 0ACH
YO_YING         = 0ADH
DO_CHADA        = 0AEH
TO_PATAK        = 0AFH
THO_THAN        = 0B0H
THO_NANGMONTHO  = 0B1H
THO_PHUTHAO     = 0B2H
NO_NEN          = 0B3H
DO_DEK          = 0B4H
TO_TAO          = 0B5H
THO_THUNG       = 0B6H
THO_THAHAN      = 0B7H
THO_THONG       = 0B8H
NO_NU           = 0B9H
BO_BAIMAI       = 0BAH
PO_PLA          = 0BBH
PHO_PHUNG       = 0BCH
FO_FA           = 0BDH
PHO_PHAN        = 0BEH
FO_FAN          = 0BFH
PHO_SAMPHAO     = 0C0H
MO_MA           = 0C1H
YO_YAK          = 0C2H
RO_RUA          = 0C3H
RU              = 0C4H
LO_LING         = 0C5H
LU              = 0C6H
WO_WAEN         = 0C7H
SO_SALA         = 0C8H
SO_RUSI         = 0C9H
SO_SUA          = 0CAH
HO_HIP          = 0CBH
LO_CHULA        = 0CCH
O_ANG           = 0CDH
HO_NOK_HUK      = 0CEH

        ;--------;
        ; Vowels ;
        ;--------;
SARA_A          = 0D0H
MAI_HAN_AKAT    = 0D1H
SARA_AA         = 0D2H
SARA_AM         = 0D3H
SARA_I          = 0D4H
SARA_II         = 0D5H
SARA_UE         = 0D6H
SARA_UEE        = 0D7H
SARA_U          = 0D8H
SARA_UU         = 0D9H
PHINTHU         = 0DAH
SARA_E          = 0E0H
SARA_EE         = 0E1H
SARA_O          = 0E2H
SARA_MAI_MUAN   = 0E3H
SARA_MAI_MALAI  = 0E4H
MAI_TAI_KHU     = 0E7H
THANTHAKHAT     = 0ECH
NIKKHAHIT       = 0EDH

        ;---------;
        ; Signs   ;
        ;---------;
PAI_YAN_NOI     = 0CFH
LAK_KHANG_YAO   = 0E5H
MAI_YAMOK       = 0E6H

        ;------------;
        ; Tone Marks ;
        ;------------;
MAI_EK          = 0E8H
MAI_THO         = 0E9H
MAI_TRI         = 0EAH
MAI_CHATTAWA    = 0EBH

        ;----------;
        ; Numerics ;
        ;----------;
THAI_ZERO       = 0F0H
THAI_ONE        = 0F1H
THAI_TWO        = 0F2H
THAI_THREE      = 0F3H
THAI_FOUR       = 0F4H
THAI_FIVE       = 0F5H
THAI_SIX        = 0F6H
THAI_SEVEN      = 0F7H
THAI_EIGHT      = 0F8H
THAI_NINE       = 0F9H

        ;----------;
        ; Currency ;
        ;----------;
BAHT            = 0DFH

;======================================================================
; Thai characters XOR 5
;======================================================================
        ;------------;
        ; Consonants ;
        ;------------;
_THAI_SPACE     = THAI_SPACE     XOR 5
_KO_KAI         = KO_KAI         XOR 5
_KHO_KHAI       = KHO_KHAI       XOR 5
_KHO_KHUAT      = KHO_KHUAT      XOR 5
_KHO_KHWAI      = KHO_KHWAI      XOR 5
_KHO_KHON       = KHO_KHON       XOR 5
_KHO_RAKHANG    = KHO_RAKHANG    XOR 5
_NGO_NGU        = NGO_NGU        XOR 5
_CHO_CHAN       = CHO_CHAN       XOR 5
_CHO_CHING      = CHO_CHING      XOR 5
_CHO_CHANG      = CHO_CHANG      XOR 5
_SO_SO          = SO_SO          XOR 5
_CHO_CHOE       = CHO_CHOE       XOR 5
_YO_YING        = YO_YING        XOR 5
_DO_CHADA       = DO_CHADA       XOR 5
_TO_PATAK       = TO_PATAK       XOR 5
_THO_THAN       = THO_THAN       XOR 5
_THO_NANGMONTHO = THO_NANGMONTHO XOR 5
_THO_PHUTHAO    = THO_PHUTHAO    XOR 5
_NO_NEN         = NO_NEN         XOR 5
_DO_DEK         = DO_DEK         XOR 5
_TO_TAO         = TO_TAO         XOR 5
_THO_THUNG      = THO_THUNG      XOR 5
_THO_THAHAN     = THO_THAHAN     XOR 5
_THO_THONG      = THO_THONG      XOR 5
_NO_NU          = NO_NU          XOR 5
_BO_BAIMAI      = BO_BAIMAI      XOR 5
_PO_PLA         = PO_PLA         XOR 5
_PHO_PHUNG      = PHO_PHUNG      XOR 5
_FO_FA          = FO_FA          XOR 5
_PHO_PHAN       = PHO_PHAN       XOR 5
_FO_FAN         = FO_FAN         XOR 5
_PHO_SAMPHAO    = PHO_SAMPHAO    XOR 5
_MO_MA          = MO_MA          XOR 5
_YO_YAK         = YO_YAK         XOR 5
_RO_RUA         = RO_RUA         XOR 5
_RU             = RU             XOR 5
_LO_LING        = LO_LING        XOR 5
_LU             = LU             XOR 5
_WO_WAEN        = WO_WAEN        XOR 5
_SO_SALA        = SO_SALA        XOR 5
_SO_RUSI        = SO_RUSI        XOR 5
_SO_SUA         = SO_SUA         XOR 5
_HO_HIP         = HO_HIP         XOR 5
_LO_CHULA       = LO_CHULA       XOR 5
_O_ANG          = O_ANG          XOR 5
_HO_NOK_HUK     = HO_NOK_HUK     XOR 5

        ;--------;
        ; Vowels ;
        ;--------;
_SARA_A         = SARA_A         XOR 5
_MAI_HAN_AKAT   = MAI_HAN_AKAT   XOR 5
_SARA_AA        = SARA_AA        XOR 5
_SARA_AM        = SARA_AM        XOR 5
_SARA_I         = SARA_I         XOR 5
_SARA_II        = SARA_II        XOR 5
_SARA_UE        = SARA_UE        XOR 5
_SARA_UEE       = SARA_UEE       XOR 5
_SARA_U         = SARA_U         XOR 5
_SARA_UU        = SARA_UU        XOR 5
_PHINTHU        = PHINTHU        XOR 5
_SARA_E         = SARA_E         XOR 5
_SARA_EE        = SARA_EE        XOR 5
_SARA_O         = SARA_O         XOR 5
_SARA_MAI_MUAN  = SARA_MAI_MUAN  XOR 5
_SARA_MAI_MALAI = SARA_MAI_MALAI XOR 5
_MAI_TAI_KHU    = MAI_TAI_KHU    XOR 5
_THANTHAKHAT    = THANTHAKHAT    XOR 5
_NIKKHAHIT      = NIKKHAHIT      XOR 5

        ;---------;
        ; Signs   ;
        ;---------;
_PAI_YAN_NOI    = PAI_YAN_NOI   XOR 5
_LAK_KHANG_YAO  = LAK_KHANG_YAO XOR 5
_MAI_YAMOK      = MAI_YAMOK     XOR 5

        ;------------;
        ; Tone Marks ;
        ;------------;
_MAI_EK         = MAI_EK       XOR 5
_MAI_THO        = MAI_THO      XOR 5
_MAI_TRI        = MAI_TRI      XOR 5
_MAI_CHATTAWA   = MAI_CHATTAWA XOR 5

        ;----------;
        ; Numerics ;
        ;----------;
_THAI_ZERO      = THAI_ZERO  XOR 5
_THAI_ONE       = THAI_ONE   XOR 5
_THAI_TWO       = THAI_TWO   XOR 5
_THAI_THREE     = THAI_THREE XOR 5
_THAI_FOUR      = THAI_FOUR  XOR 5
_THAI_FIVE      = THAI_FIVE  XOR 5
_THAI_SIX       = THAI_SIX   XOR 5
_THAI_SEVEN     = THAI_SEVEN XOR 5
_THAI_EIGHT     = THAI_EIGHT XOR 5
_THAI_NINE      = THAI_NINE  XOR 5

        ;----------;
        ; Currency ;
        ;----------;
_BAHT           = BAHT XOR 5

;======================================================================
; PRINTER TYPE
;======================================================================
EPSON = 0
IBMPRO = 1

GRAPHICS_ADDRESS_REG  = 03CEH
GRAPHICS_DATA_REG     = 03CFH

ENGLISH = 0
THAI_8 = 1
THAI_25 = 2

ENGPRINT = 0
THAIPRT1 = 1
THAIPRT3 = 2
THAIPRT4 = 3

.xcref
.xlist

;=============================================================================
;
;     Macro definition file compatible with MASM v5.1.
;
;     These provide the definitions that the assembler needs to assemble the
;     intrinsic and standard user-preference macros as supplied with MD86 v2.3.
;
;     Macro to push a variable number of registers.
;
_push macro r1,r2,r3,r4,r5,r6,r7,r8,r9
     irp reg,<r1,r2,r3,r4,r5,r6,r7,r8,r9>
       ifdef reg
       push reg
       endif
     endm
    endm
;
;     Macro to pop a variable number of registers.
;
_pop macro r1,r2,r3,r4,r5,r6,r7,r8,r9
     irp reg,<r1,r2,r3,r4,r5,r6,r7,r8,r9>
       ifdef reg
       pop  reg
       endif
     endm
    endm

;
;    Conditional jumps with a destination beyond the 128 byte limit. These
;    use a near jump instead.
;
_JZ    macro  arg
       local  skip
       jnz    skip
       jmp    arg
skip:
       endm
_JNZ   macro  arg
       local  skip
       jz     skip
       jmp    arg
skip:
       endm
_JC    macro  arg
       local  skip
       jnc    skip
       jmp    arg
skip:
       endm
_JNC   macro  arg
       local  skip
       jc     skip
       jmp    arg
skip:
       endm
;
;    Shifts with a bit count greater than 1. This will use the CL register as
;    a counter.
;
_SHR   macro  reg,arg
       mov    cl,arg
       shr    reg,cl
       endm
_SHL   macro  reg,arg
       mov    cl,arg
       shl    reg,cl
       endm
_SAR   macro  reg,arg
       mov    cl,arg
       sar    reg,cl
       endm
_ROL   macro  reg,arg
       mov    cl,arg
       rol    reg,cl
       endm
_ROR   macro  reg,arg
       mov    cl,arg
       ror    reg,cl
       endm
.cref
.list


; VGA-only display geometry (25 rows occupy 475 of 480 scanlines).
; Visible frame wraps at 64K: E000h..FFFFh, 0000h..75FFh.
; Reserve VGA 8000h..DFFFh for B800:0000..5FFFh (six text pages).
VGA_ORIGIN = 0E000H












