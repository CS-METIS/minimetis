import ipyvuetify as v
import traitlets
import datetime

template = """
    <v-menu
        v-model="menu"
        :close-on-content-click="false"
        :nudge-right="40"
        transition="scale-transition"
        offset-y
        min-width="290px"
        dark
      >
        <template v-slot:activator="{ on, attrs }">
          <v-text-field
            v-model="v_model"
            :label="label"
            prepend-icon="mdi-calendar"
            readonly
            v-bind="attrs"
            v-on="on"          >
          </v-text-field>
        </template>
        <v-date-picker
        
          v-model="v_model"
          dark
          @input="menu = false"
          @input=date_click()
        >
        </v-date-picker>
      </v-menu>
"""
class DatePicker(v.VuetifyTemplate):
    
    v_model = traitlets.Unicode(str(datetime.date.today())).tag(sync=True)
    template = traitlets.Unicode(template).tag(sync=True)
    
    menu = traitlets.Bool(False).tag(sync=True)
    label = traitlets.Unicode('Select date').tag(sync=True)

    def __init__(self,**kwargs):
        super().__init__(**kwargs)