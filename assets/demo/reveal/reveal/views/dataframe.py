import pandas as pd
import traitlets
import ipyvuetify as v
import json
import typing as t

# data = pd.DataFrame.from_dict(res.result)
# data.set_index(["@rid"], drop=True, inplace=True)
# data = data[["no_voie", "type_de_voie", "voie", "code_postal", "commune"]]

#         # https://stackoverflow.com/questions/57961043/how-does-one-style-a-specific-row-on-v-data-table-vuetify


class DataFrameView(v.VuetifyTemplate):
    """
    Vuetify DataTable rendering of a pandas DataFrame
    
    Args:
        data (DataFrame) - the data to render
        title (str) - optional title
    """
    
    headers = traitlets.List([]).tag(sync=True, allow_null=True)
    items = traitlets.List([]).tag(sync=True, allow_null=True)
    search = traitlets.Unicode('').tag(sync=True)
    title = traitlets.Unicode('DataFrame').tag(sync=True)
    index_col = traitlets.Unicode('').tag(sync=True)
    template = traitlets.Unicode('''
        <template>
          <v-card>
            <v-card-title>
              <span class="title font-weight-bold">{{ title }}</span>
              <v-spacer></v-spacer>
                <v-text-field
                    v-model="search"
                    append-icon="mdi-magnify"
                    label="Search ..."
                    single-line
                    hide-details
                ></v-text-field>
            </v-card-title>
            <v-data-table
                dense
                :headers="headers"
                :items="items"
                :search="search"
                :item-key="index_col"
                :footer-props="{'items-per-page-options': [25, 50, 250, 500]}"
                @click:row="row_clicked"
            >
                <template v-slot:no-data>
                  <v-alert :value="true" color="#F3F3F3" icon="mdi-alert" dense>
                    Configurer les filtres pour afficher les données
                  </v-alert>
                </template>
                <template v-slot:no-results>
                    <v-alert :value="true" color="error" icon="mdi-alert" dense>
                      Your search for "{{ search }}" found no results.
                    </v-alert>
                </template>
                <template v-slot:items="rows">
                  <td v-for="(element, label, index) in rows.item"
                      @click="cell_click(element)"
                      >
                    {{ element }}
                  </td>
                </template>
            </v-data-table>
          </v-card>
        </template>
        ''').tag(sync=True)
    
    def __init__(self, *args,
                 on_item_selected: t.Callable[[str], None],
                 data: pd.DataFrame = pd.DataFrame(), 
                 title: str = "",
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.on_item_selected = on_item_selected
        data = data.reset_index()
        self.index_col = data.columns[0]
        headers = [{
              "text": col,
              "value": col
            } for col in data.columns]
        headers[0].update({'align': 'left', 'sortable': True})
        self.headers = headers
        self.items = data.to_dict(orient='records')
        if title is not None:
            self.title = title

    def vue_row_clicked(self, row):
      self.on_item_selected(row)

    def update(self, data):
        data = data.reset_index()
        self.index_col = data.columns[0]
        headers = [{
              "text": col,
              "value": col
            } for col in data.columns]
        headers[0].update({'align': 'left', 'sortable': True})
        self.headers = headers
        self.items = data.to_dict(orient='records')

def create(on_item_selected: t.Callable[[str], None]) -> DataFrameView:
  return DataFrameView(on_item_selected=on_item_selected)